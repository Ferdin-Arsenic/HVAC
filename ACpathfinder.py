import heapq
import os
from collections import deque
from typing import List, Tuple, Optional, Set, Dict
import time
import copy
import sys

class ACPathfinder:
    def __init__(self, building_matrix: List[List[List[str]]]):
        """
        Inisialisasi pathfinder dengan matriks gedung 3D
        Format: [lantai][baris][kolom]
        S = Sumber AC, R = Ruangan tujuan, . = Area kosong, W = Dinding/halangan, T = Tangga/Lift
        """
        self.building = building_matrix
        self.floors = len(building_matrix)
        self.rows = len(building_matrix[0]) if building_matrix else 0
        self.cols = len(building_matrix[0][0]) if building_matrix and building_matrix[0] else 0
        
        # Cari posisi sumber dan tujuan
        self.source = self._find_position('S')
        self.targets = self._find_all_positions('R')
        self.stairs = self._find_all_positions('T')
        
        # Arah pergerakan: atas, bawah, kiri, kanan
        self.directions = [
            (-1, 0),  # Atas (baris berkurang)
            (1, 0),   # Bawah (baris bertambah)
            (0, -1),  # Kiri (kolom berkurang)
            (0, 1)    # Kanan (kolom bertambah)
        ]
        
        # Biaya energi untuk setiap jenis pergerakan
        self.energy_costs = {
            'horizontal': 1.0,      # Gerakan horizontal (kiri/kanan/atas/bawah di lantai sama)
            'vertical_up': 3.0,     # Naik lantai melalui tangga/lift
            'vertical_down': 2.0,   # Turun lantai melalui tangga/lift
            'turn': 0.5,           # Biaya tambahan untuk berbelok
            'base_pressure': 0.1    # Biaya dasar tekanan per unit panjang
        }
    
    def _find_position(self, symbol: str) -> Optional[Tuple[int, int, int]]:
        """Mencari posisi symbol tertentu dalam matriks"""
        for f in range(self.floors):
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.building[f][r][c] == symbol:
                        return (f, r, c)
        return None
    
    def _find_all_positions(self, symbol: str) -> List[Tuple[int, int, int]]:
        """Mencari semua posisi symbol tertentu dalam matriks"""
        positions = []
        for f in range(self.floors):
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.building[f][r][c] == symbol:
                        positions.append((f, r, c))
        return positions
    
    def _is_valid_position(self, f: int, r: int, c: int) -> bool:
        """Mengecek apakah posisi valid dan bukan dinding"""
        return (0 <= f < self.floors and 
                0 <= r < self.rows and 
                0 <= c < self.cols and 
                self.building[f][r][c] != 'W')
    
    def _can_change_floor(self, current_pos: Tuple[int, int, int], target_floor: int) -> bool:
        """Mengecek apakah bisa pindah lantai dari posisi current ke target floor"""
        f, r, c = current_pos
        
        # Harus ada tangga/lift di posisi current atau posisi yang akan dituju
        if self.building[f][r][c] == 'T':
            return True
        
        # Cek apakah ada tangga/lift di lantai tujuan dengan koordinat yang sama
        if (0 <= target_floor < self.floors and 
            0 <= r < self.rows and 
            0 <= c < self.cols and
            self.building[target_floor][r][c] == 'T'):
            return True
            
        return False
    
    def _calculate_energy_cost(self, path: List[Tuple[int, int, int]]) -> float:
        """Menghitung total biaya energi untuk sebuah jalur"""
        if len(path) < 2:
            return 0.0
        
        total_energy = 0.0
        
        for i in range(1, len(path)):
            prev_pos = path[i-1]
            curr_pos = path[i]
            
            prev_f, prev_r, prev_c = prev_pos
            curr_f, curr_r, curr_c = curr_pos
            
            # Biaya dasar tekanan
            total_energy += self.energy_costs['base_pressure']
            
            # Biaya pergerakan
            if curr_f != prev_f:
                # Pergerakan vertikal (naik/turun lantai)
                if curr_f > prev_f:
                    total_energy += self.energy_costs['vertical_up']
                else:
                    total_energy += self.energy_costs['vertical_down']
            else:
                # Pergerakan horizontal
                total_energy += self.energy_costs['horizontal']
            
            # Biaya berbelok
            if i >= 2:
                prev_prev_pos = path[i-2]
                if self._is_turn(prev_prev_pos, prev_pos, curr_pos):
                    total_energy += self.energy_costs['turn']
        
        return total_energy
    
    def _is_turn(self, pos1: Tuple[int, int, int], pos2: Tuple[int, int, int], pos3: Tuple[int, int, int]) -> bool:
        """Mengecek apakah terjadi belokan dari pos1 ke pos2 ke pos3"""
        # Arah dari pos1 ke pos2
        dir1 = (pos2[0] - pos1[0], pos2[1] - pos1[1], pos2[2] - pos1[2])
        # Arah dari pos2 ke pos3
        dir2 = (pos3[0] - pos2[0], pos3[1] - pos2[1], pos3[2] - pos2[2])
        
        # Jika arah berbeda, maka terjadi belokan
        return dir1 != dir2
    
    def _expand_path(self, path: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Mengubah jalur renggang (waypoints) menjadi jalur padat (langkah per langkah)
        untuk keperluan visualisasi.
        """
        if len(path) < 2:
            return path

        dense_path = [path[0]]
        for i in range(len(path) - 1):
            start_pos = path[i]
            end_pos = path[i+1]

            f1, r1, c1 = start_pos
            f2, r2, c2 = end_pos

            # Jika pindah lantai, tidak ada titik antara
            if f1 != f2:
                dense_path.append(end_pos)
                continue

            # Jika bergerak vertikal (atas/bawah) di lantai yang sama
            if c1 == c2:
                step = 1 if r2 > r1 else -1
                for r in range(r1 + step, r2, step):
                    dense_path.append((f1, r, c1))
            # Jika bergerak horizontal (kiri/kanan) di lantai yang sama
            elif r1 == r2:
                step = 1 if c2 > c1 else -1
                for c in range(c1 + step, c2, step):
                    dense_path.append((f1, r1, c))
            
            dense_path.append(end_pos)
        
        return dense_path
    
    def bfs_pathfinding(self) -> List[Dict]:
        """
        Algoritma BFS untuk mencari jalur terpendek ke semua ruangan tujuan
        dengan perhitungan energi. (Versi Perbaikan)
        """
        if not self.source or not self.targets:
            return []
        
        paths_to_all_targets = []
        
        for target_idx, target in enumerate(self.targets):
            # Antrian menyimpan: (posisi_sekarang, path_sejauh_ini)
            queue = deque([(self.source, [self.source])])
            visited = {self.source}
            
            path_found = False
            
            while queue:
                current_pos, path = queue.popleft()
                
                # Jika target ditemukan
                if current_pos == target:
                    energy_cost = self._calculate_energy_cost(path)
                    path_info = {
                        'target_index': target_idx,
                        'target_position': target,
                        'path': path,
                        'steps': len(path),
                        'energy_cost': energy_cost
                    }
                    paths_to_all_targets.append(path_info)
                    path_found = True
                    break # Keluar dari while loop karena jalur ke target ini sudah ditemukan
                
                f, r, c = current_pos
                
                # Opsi 1: Pergerakan horizontal di lantai yang sama
                for dr, dc in self.directions: # Menggunakan arah 2D
                    new_r, new_c = r + dr, c + dc
                    new_pos = (f, new_r, new_c) # Lantai (f) tetap sama
                    
                    if self._is_valid_position(f, new_r, new_c) and new_pos not in visited:
                        visited.add(new_pos)
                        new_path = path + [new_pos]
                        queue.append((new_pos, new_path))
                
                # Opsi 2: Pergerakan vertikal (pindah lantai) HANYA di posisi tangga
                if self.building[f][r][c] == 'T':
                    for new_f in range(self.floors):
                        if new_f != f: # Cek lantai lain
                            # Pastikan di lantai tujuan juga ada tangga di posisi yang sama
                            if self.building[new_f][r][c] == 'T':
                                new_pos = (new_f, r, c)
                                if new_pos not in visited:
                                    visited.add(new_pos)
                                    new_path = path + [new_pos]
                                    queue.append((new_pos, new_path))

            if not path_found:
                print(f"BFS: Tidak dapat menemukan jalur ke ruangan di {target}")
        
        return paths_to_all_targets

    def optimize_energy_usage(self, path_info_list: List[Dict]) -> List[Dict]:
        """
        Mengoptimalkan penggunaan energi dengan mencari jalur alternatif
        """
        optimized_paths = []
        
        for path_info in path_info_list:
            original_path = path_info['path']
            original_energy = path_info['energy_cost']
            
            # Coba optimasi dengan menghindari belokan yang tidak perlu
            optimized_path = self._optimize_path_turns(original_path)
            optimized_energy = self._calculate_energy_cost(optimized_path)
            
            # Gunakan jalur yang lebih efisien
            if optimized_energy < original_energy:
                optimized_info = path_info.copy()
                optimized_info['path'] = optimized_path
                optimized_info['energy_cost'] = optimized_energy
                optimized_info['steps'] = len(optimized_path)
                optimized_info['energy_saved'] = original_energy - optimized_energy
                optimized_paths.append(optimized_info)
            else:
                path_info['energy_saved'] = 0.0
                optimized_paths.append(path_info)
        
        return optimized_paths
    
    def _optimize_path_turns(self, path: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Mengoptimalkan jalur dengan mengurangi belokan yang tidak perlu
        """
        if len(path) <= 2:
            return path
        
        optimized = [path[0]]
        
        for i in range(1, len(path) - 1):
            prev_pos = optimized[-1]
            curr_pos = path[i]
            next_pos = path[i + 1]
            
            # Cek apakah bisa langsung ke next_pos tanpa melalui curr_pos
            if self._can_go_direct(prev_pos, next_pos):
                # Skip curr_pos jika memungkinkan
                continue
            else:
                optimized.append(curr_pos)
        
        optimized.append(path[-1])
        return optimized
    
    def _can_go_direct(self, pos1: Tuple[int, int, int], pos2: Tuple[int, int, int]) -> bool:
        """
        Mengecek apakah bisa langsung dari pos1 ke pos2 tanpa halangan
        """
        f1, r1, c1 = pos1
        f2, r2, c2 = pos2
        
        # Hanya untuk pergerakan horizontal di lantai yang sama
        if f1 != f2:
            return False
        
        # Hanya untuk pergerakan lurus (horizontal atau vertikal)
        if (r1 != r2 and c1 != c2):
            return False
        
        # Cek apakah ada halangan di antara pos1 dan pos2
        if r1 == r2:  # Pergerakan horizontal
            start_c = min(c1, c2)
            end_c = max(c1, c2)
            for c in range(start_c + 1, end_c):
                if not self._is_valid_position(f1, r1, c):
                    return False
        else:  # Pergerakan vertikal
            start_r = min(r1, r2)
            end_r = max(r1, r2)
            for r in range(start_r + 1, end_r):
                if not self._is_valid_position(f1, r, c1):
                    return False
        
        return True
    
    def print_building(self):
        """Menampilkan representasi gedung"""
        print("=== DENAH GEDUNG ===")
        for f in range(self.floors):
            print(f"\nLantai {f + 1}:")
            for r in range(self.rows):
                print(" ".join(self.building[f][r]))
    
    def print_path_with_energy(self, path_info: Dict, algorithm: str):
        """Menampilkan jalur yang ditemukan dengan informasi energi"""
        if not path_info or not path_info['path']:
            print(f"{algorithm}: Tidak ada jalur yang ditemukan")
            return
        
        path = path_info['path']
        energy_cost = path_info['energy_cost']
        target_idx = path_info['target_index']
        
        print(f"\n=== JALUR {algorithm} ke Ruangan {target_idx + 1} ===")
        print(f"Panjang jalur: {len(path)} langkah")
        print(f"Biaya energi: {energy_cost:.2f} unit")
        print(f"Efisiensi energi: {energy_cost/len(path):.2f} unit per langkah")
        
        if path_info.get('energy_saved', 0) > 0:
            print(f"Penghematan energi: {path_info['energy_saved']:.2f} unit")
        
        print("Koordinat jalur (Lantai, Baris, Kolom):")
        for i, (f, r, c) in enumerate(path):
            cell_type = self.building[f][r][c]
            type_desc = ""
            if cell_type == 'S':
                type_desc = " [Sumber AC]"
            elif cell_type == 'R':
                type_desc = " [Ruangan Tujuan]"
            elif cell_type == 'T':
                type_desc = " [Tangga/Lift]"
            
            print(f"  {i + 1}. Lantai {f + 1}, Baris {r + 1}, Kolom {c + 1}{type_desc}")
    
    def create_professional_blueprint(self, paths_info: List[Dict], algorithm: str):
        """
        Membuat blueprint profesional yang rapi dan padat dengan informasi energi.
        (Versi Revisi)
        """
        if not paths_info:
            print(f"\n{algorithm}: Tidak ada jalur untuk divisualisasikan")
            return

        print(f"\n{'='*80}")
        print(f"BLUEPRINT INSTALASI PIPA AC - {algorithm}".center(80))
        print(f"{'='*80}")

        # Gabungkan semua koordinat path untuk memudahkan pengecekan
        all_path_coords = set()
        for info in paths_info:
            # Pastikan menggunakan visual_path jika ada
            path_to_use = info.get('visual_path', info['path'])
            for pos in path_to_use:
                all_path_coords.add(pos)
        
        for floor_idx in range(self.floors):
            self._draw_floor_blueprint_revised(floor_idx, paths_info, all_path_coords)
        
        self._draw_energy_legend(paths_info, [])

    def _draw_floor_blueprint_revised(self, floor_idx: int, paths_info: List[Dict], all_path_coords: set):
        """Menggambar blueprint untuk satu lantai dengan format yang padat dan rapi."""
        print(f"\n--- LANTAI {floor_idx + 1} ---")

        # Buat canvas dasar untuk lantai ini
        # Setiap sel akan direpresentasikan sebagai satu karakter
        canvas = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]

        # 1. Gambar elemen dasar gedung (Tembok, Ruangan, dll.)
        for r in range(self.rows):
            for c in range(self.cols):
                symbol = self.building[floor_idx][r][c]
                if symbol == 'W':
                    canvas[r][c] = '█'
                elif symbol == 'S':
                    canvas[r][c] = 'S'
                elif symbol == 'R':
                    canvas[r][c] = 'R'
                elif symbol == 'T':
                    canvas[r][c] = 'T'
                elif (floor_idx, r, c) not in all_path_coords:
                     canvas[r][c] = '·'

        # 2. Gambar jalur pipa di atas canvas
        for info in paths_info:
            path = info.get('visual_path', info['path'])
            for i, pos in enumerate(path):
                f, r, c = pos
                if f == floor_idx:
                    # Dapatkan karakter pipa yang sesuai (belokan, lurus, dll.)
                    path_char = self._get_path_char_for_pos(pos, path)
                    canvas[r][c] = path_char

        # 3. Cetak canvas ke terminal dengan border dan nomor
        # Header kolom
        header = "    " + "".join([f"{c+1:^3}" for c in range(self.cols)])
        print(header)
        print("  ┌" + "─" * (self.cols * 3) + "┐")

        for r in range(self.rows):
            row_str = f"{r+1:<2}│"
            for c in range(self.cols):
                char = canvas[r][c]
                # Beri warna untuk membedakan elemen (opsional, butuh library seperti colorama)
                row_str += f" {char} "
            row_str += "│"
            print(row_str)
        
        print("  └" + "─" * (self.cols * 3) + "┘")

    def _get_path_char_for_pos(self, pos: Tuple[int, int, int], path: List[Tuple[int, int, int]]) -> str:
        """Menentukan karakter pipa yang tepat (lurus, belokan, dll.) untuk sebuah posisi."""
        f, r, c = pos
        
        # Jika posisi adalah Sumber, Ruangan, atau Tangga, prioritaskan simbol itu
        symbol = self.building[f][r][c]
        if symbol in ('S', 'R', 'T'):
            return symbol

        try:
            idx = path.index(pos)
        except ValueError:
            return '·' # Seharusnya tidak terjadi

        # Cek koneksi ke titik sebelum dan sesudahnya
        has_up = has_down = has_left = has_right = False

        # Koneksi ke titik sebelumnya
        if idx > 0:
            pf, pr, pc = path[idx - 1]
            if f == pf: # Hanya jika di lantai yang sama
                if pr < r: has_up = True
                if pr > r: has_down = True
                if pc < c: has_left = True
                if pc > c: has_right = True
        
        # Koneksi ke titik sesudahnya
        if idx < len(path) - 1:
            nf, nr, nc = path[idx + 1]
            if f == nf: # Hanya jika di lantai yang sama
                if nr < r: has_up = True
                if nr > r: has_down = True
                if nc < c: has_left = True
                if nc > c: has_right = True

        # Tentukan karakter berdasarkan koneksi
        if has_up and has_down: return '│'
        if has_left and has_right: return '─'
        if has_down and has_right: return '┌'
        if has_down and has_left: return '┐'
        if has_up and has_right: return '└'
        if has_up and has_left: return '┘'
        
        # Jika ada koneksi ke 4 arah (persimpangan)
        if (has_up or has_down) and (has_left or has_right): return '┼'
        
        # Jika hanya satu koneksi (ujung path di lantai itu)
        if has_up or has_down: return '│'
        if has_left or has_right: return '─'

        return '·' # Fallback
    
    
    def _get_cell_content(self, floor_idx: int, row: int, col: int, paths: List[List[Tuple[int, int, int]]], path_styles: List[Tuple[str]], line: int) -> str:
        """Mendapatkan konten untuk sebuah sel dengan prioritas pada ikon dan padding yang benar."""
        cell_width = 8
        cell = self.building[floor_idx][row][col]
        path_info = self._get_path_info(floor_idx, row, col, paths)

        if line == 1:  # Baris tengah sel, tempat konten utama
            # Prioritas 1: Tampilkan ikon untuk lokasi-lokasi penting (lebar 8 karakter)
            if cell == 'S': return f"   🏠    "
            if cell == 'R': return f"   🎯    "
            if cell == 'T': return f"   🏗️    "
            if cell == 'W': return f"  ████  "
            
            # Prioritas 2: Jika bukan lokasi penting, gambar jalur pipa
            if path_info:
                return self._draw_path_connections(floor_idx, row, col, paths, path_styles)

            # Prioritas 3: Jika tidak ada apa-apa, gambar area kosong
            return f"   ·    "

        # Gambar koneksi vertikal untuk jalur pipa
        elif (line == 0 or line == 2) and path_info:
            connections_up = self._has_vertical_connection(floor_idx, row, col, paths, is_top=True)
            connections_down = self._has_vertical_connection(floor_idx, row, col, paths, is_top=False)
            if (line == 0 and connections_up) or (line == 2 and connections_down):
                path_idx = path_info[0]
                # Ambil karakter vertikal dari style
                style_idx = path_idx % len(path_styles)
                v_char = path_styles[style_idx][1]
                return f"   {v_char}    "
        
        return " " * cell_width
    
    def _get_path_info(self, floor_idx: int, row: int, col: int, paths: List[List[Tuple[int, int, int]]]) -> Optional[List[int]]:
        """Mendapatkan informasi jalur yang melewati posisi ini"""
        path_indices = []
        for i, path in enumerate(paths):
            if (floor_idx, row, col) in path:
                path_indices.append(i)
        return path_indices if path_indices else None
    
    def _draw_path_connections(self, floor_idx: int, row: int, col: int, paths: List[List[Tuple[int, int, int]]], path_styles: List[Tuple[str]]) -> str:
        """Menggambar koneksi jalur dengan padding yang benar untuk memastikan lebar 8 karakter."""
        path_nums = self._get_path_info(floor_idx, row, col, paths)
        
        if not path_nums:
            return " " * 8

        # Tentukan gaya berdasarkan path pertama yang melewati sel ini
        style_idx = path_nums[0] % len(path_styles)
        h_char, v_char, tl, tr, bl, br, cross = path_styles[style_idx]
        
        connections = {'up': False, 'down': False, 'left': False, 'right': False}
        # Cek koneksi untuk SEMUA jalur yang melewati sel ini
        for path_idx in path_nums:
            path = paths[path_idx]
            pos_index = path.index((floor_idx, row, col))
            
            if pos_index > 0:
                prev_f, prev_r, prev_c = path[pos_index - 1]
                if prev_f == floor_idx:
                    if prev_r < row: connections['up'] = True
                    elif prev_r > row: connections['down'] = True
                    elif prev_c < col: connections['left'] = True
                    elif prev_c > col: connections['right'] = True
            
            if pos_index < len(path) - 1:
                next_f, next_r, next_c = path[pos_index + 1]
                if next_f == floor_idx:
                    if next_r < row: connections['up'] = True
                    elif next_r > row: connections['down'] = True
                    elif next_c < col: connections['left'] = True
                    elif next_c > col: connections['right'] = True

        # Tentukan karakter tengah (mid) berdasarkan koneksi
        up, down, left_conn, right_conn = connections['up'], connections['down'], connections['left'], connections['right']
        
        mid = "●" # Default untuk titik tunggal
        if up and down and left_conn and right_conn: mid = cross
        elif up and down: mid = v_char
        elif left_conn and right_conn: mid = h_char[0]
        elif up and left_conn: mid = br
        elif up and right_conn: mid = bl
        elif down and left_conn: mid = tr
        elif down and right_conn: mid = tl
        elif up or down: mid = v_char
        elif left_conn or right_conn: mid = h_char[0]

        # Buat bagian kiri dan kanan
        left = h_char if left_conn else "  "
        right = h_char if right_conn else "  "
        
        # Gabungkan dan pastikan lebarnya 8
        core_content = f"{left}{mid}{right}"
        return f" {core_content} "
    
    def _has_vertical_connection(self, floor_idx: int, row: int, col: int, paths: List[List[Tuple[int, int, int]]], is_top: bool) -> bool:
        """Cek apakah ada koneksi vertikal ke atas atau ke bawah dari sel ini."""
        target_row = row - 1 if is_top else row + 1
        
        for path in paths:
            try:
                # Cek apakah posisi saat ini dan posisi target (atas/bawah) ada di jalur yang sama
                current_pos_index = path.index((floor_idx, row, col))
                target_pos_index = path.index((floor_idx, target_row, col))
                
                # Pastikan mereka bersebelahan di dalam path
                if abs(current_pos_index - target_pos_index) == 1:
                    return True
            except ValueError:
                # Salah satu posisi tidak ada di jalur ini, lanjutkan ke path berikutnya
                continue
        return False
    
    def _draw_energy_legend(self, paths_info: List[Dict], path_styles: List[str]):
        """
        Menggambar legend blueprint dengan informasi energi dalam format tabel yang rapi.
        (Versi Revisi 2)
        """
        # --- Helper Function untuk mencetak baris dengan border ---
        def print_line(text="", align='left', width=76):
            if align == 'center':
                content = text.center(width)
            else:
                content = text.ljust(width)
            print(f"│ {content} │")

        def print_separator(width=76):
            print(f"├{'─' * (width + 2)}┤")
        
        WIDTH = 76
        
        print(f"\n{'='*80}")
        print("KETERANGAN BLUEPRINT & ANALISIS ENERGI".center(80))
        print(f"{'='*80}")
        
        # --- Gambar Tabel ---
        print(f"┌{'─' * (WIDTH + 2)}┐")
        
        print_line("LEGENDA SIMBOL", align='center', width=WIDTH)
        print_separator(width=WIDTH)
        print_line("S = Sumber AC (Outdoor Unit)", width=WIDTH)
        print_line("R = Ruangan Tujuan (Indoor Unit)", width=WIDTH)
        print_line("T = Tangga/Lift (Akses Vertikal)", width=WIDTH)
        print_line("█ = Dinding/Halangan", width=WIDTH)
        print_line("· = Area Kosong", width=WIDTH)
        print_line("─ │ └ ┘ ┌ ┐ ┼ = Simbol Jalur Pipa (Lurus, Belokan, Persimpangan)", width=WIDTH)
        
        print_separator(width=WIDTH)
        print_line("ANALISIS JALUR OPTIMAL", align='center', width=WIDTH)
        print_separator(width=WIDTH)
        
        total_energy = 0
        total_steps = 0
        for i, path_info in enumerate(paths_info):
            energy = path_info['energy_cost']
            steps = len(path_info.get('visual_path', path_info['path']))
            efficiency = energy / steps if steps > 0 else 0
            
            info_text = f"Jalur ke Ruangan @{path_info['target_position']}: {steps} langkah, {energy:.1f} unit energi (efisiensi: {efficiency:.2f})"
            print_line(info_text, width=WIDTH)

            total_energy += energy
            total_steps += steps

        print_separator(width=WIDTH)
        print_line("BIAYA ENERGI PER JENIS", align='center', width=WIDTH)
        print_separator(width=WIDTH)
        
        cost_info = (
            f"Horizontal: {self.energy_costs['horizontal']:.1f} | "
            f"Naik: {self.energy_costs['vertical_up']:.1f} | "
            f"Turun: {self.energy_costs['vertical_down']:.1f} | "
            f"Belok: {self.energy_costs['turn']:.1f} | "
            f"Tekanan: {self.energy_costs['base_pressure']:.1f} (semua per unit)"
        )
        print_line(cost_info, width=WIDTH)
        
        print_separator(width=WIDTH)
        print_line("INFORMASI TEKNIS KESELURUHAN", align='center', width=WIDTH)
        print_separator(width=WIDTH)
        
        avg_efficiency = total_energy / total_steps if total_steps > 0 else 0
        print_line(f"Total Energi Sistem: {total_energy:.2f} unit", width=WIDTH)
        print_line(f"Total Panjang Pipa (Visual): {total_steps} unit", width=WIDTH)
        print_line(f"Efisiensi Rata-rata: {avg_efficiency:.3f} unit energi per langkah", width=WIDTH)
        print_line(f"Jumlah Ruangan: {len(paths_info)}", width=WIDTH)
        print_line(f"Jumlah Lantai: {self.floors} | Dimensi: {self.rows}x{self.cols} | Tangga/Lift: {len(self.stairs)}", width=WIDTH)

        print(f"└{'─' * (WIDTH + 2)}┘")


def read_building_from_file(filepath: str) -> List[List[List[str]]]:
    """
    Membaca matriks gedung dari file teks, memastikan semua baris rata,
    dan mengabaikan baris yang bukan bagian dari denah.
    """
    building = []
    map_chars = {'S', 'R', 'T', 'W', '.'}
    try:
        with open(filepath, 'r') as f:
            floor_data = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Jika baris adalah pemisah lantai
                if line == '---':
                    if floor_data:
                        building.append(floor_data)
                    floor_data = []
                    continue

                # Proses hanya baris yang terlihat seperti denah
                # Ambil bagian akhir dari baris (setelah ']' jika ada)
                if ']' in line:
                    line = line.split(']', 1)[-1].strip()

                # Buat baris denah dari karakter yang valid
                row = [char for char in line.replace(" ", "") if char in map_chars]
                if row: # Hanya tambahkan jika baris tidak kosong setelah dibersihkan
                    floor_data.append(row)

            if floor_data:
                building.append(floor_data)
    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di '{filepath}'")
        return []
    except Exception as e:
        print(f"Terjadi error saat membaca file: {e}")
        return []

    if not building:
        return []

    # (Sisa fungsi ini sama seperti sebelumnya, untuk meratakan kolom)
    max_cols = 0
    for floor in building:
        for row in floor:
            if len(row) > max_cols:
                max_cols = len(row)

    sanitized_building = []
    for floor in building:
        sanitized_floor = []
        for row in floor:
            current_len = len(row)
            if current_len < max_cols:
                row.extend(['.'] * (max_cols - current_len))
            sanitized_floor.append(row)
        sanitized_building.append(sanitized_floor)
    
    return sanitized_building

# --- Main execution block ---
if __name__ == "__main__":
    building_layout_file = None # Inisialisasi variabel nama file

    # Periksa apakah nama file diberikan sebagai argumen baris perintah
    if len(sys.argv) > 1:
        building_layout_file = sys.argv[1]
        print(f"[INFO] Memuat denah dari argumen: '{building_layout_file}'")
    else:
        try:
            building_layout_file = input("Masukkan nama file denah gedung (contoh: denah.txt): ")
        except KeyboardInterrupt:
            print("\nProses dibatalkan oleh pengguna. Keluar.")
            sys.exit(0)

    # Pastikan nama file tidak kosong
    if not building_layout_file:
        print("Error: Tidak ada nama file yang diberikan. Program berhenti.")
        sys.exit(1)

    # Baca dan buat matriks gedung dari file yang sudah ditentukan
    building_matrix = read_building_from_file(building_layout_file)
    
    if not building_matrix:
        print("Gagal memuat denah gedung. Pastikan nama file benar dan file ada. Program berhenti.")
    else:
        # Inisialisasi Pathfinder
        pathfinder = ACPathfinder(building_matrix)
        
        # Tampilkan denah gedung awal
        pathfinder.print_building()
        
        # 1. Jalankan algoritma BFS untuk mencari jalur
        print("\n[INFO] Menjalankan algoritma BFS untuk mencari jalur awal...")
        start_time = time.time()
        bfs_paths = pathfinder.bfs_pathfinding()
        end_time = time.time()
        print(f"[INFO] BFS selesai dalam {end_time - start_time:.4f} detik.")
        
        if bfs_paths:
            # 2. Jalankan optimasi energi
            print("\n[INFO] Menjalankan optimasi energi pada jalur yang ditemukan...")
            start_time = time.time()
            optimized_paths_info = pathfinder.optimize_energy_usage(bfs_paths)
            end_time = time.time()
            print(f"[INFO] Optimasi selesai dalam {end_time - start_time:.4f} detik.")
            
            # Tampilkan detail jalur setelah optimasi
            # Tampilkan detail jalur setelah optimasi
            for path_info in optimized_paths_info:
                 pathfinder.print_path_with_energy(path_info, "Jalur Optimal")

            # "Padatkan" setiap jalur yang sudah dioptimasi untuk visualisasi
            for info in optimized_paths_info:
                info['visual_path'] = pathfinder._expand_path(info['path'])
                 
            # Buat blueprint profesional HANYA untuk hasil optimasi
            pathfinder.create_professional_blueprint(optimized_paths_info, "BLUEPRINT HASIL OPTIMASI")

        else:
            print("\n[AKHIR] Tidak ada jalur yang ditemukan dari sumber ke ruangan tujuan.")