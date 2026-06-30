#!/usr/bin/env python3
"""
离线 PCD → 2D Occupancy Grid (PGM + YAML)

用法:
    python3 pcd_to_2d_map.py input.pcd [--output 2D_map]

输出:
    maps/2D_map.pgm         Nav2 可加载的占据栅格
    maps/2D_map.yaml
    maps/2D_map_debug.png   可视化 debug 图（红=障碍，绿=地面)
"""

import os, sys, argparse, numpy as np

# ── 可调参数 ──────────────────────────────────────────
MAP_RESOLUTION = 0.05        # 栅格分辨率 (m)
GROUND_PERCENTILE = 10       # 取最低 N% 的 Z 均值作为地面高度
GROUND_TOLERANCE = 0.10      # z < ground + tolerance → 地面
OBSTACLE_MIN_H = 0.10        # 障碍最低相对地面高度
OBSTACLE_MAX_H = 2.20        # 障碍最高相对地面高度
BLIND_RADIUS = 0.5           # 盲区半径
MAX_RANGE = 20.0             # 最大距离
MIN_OBS_POINTS = 2           # 格内至少 N 个点才标障碍
DILATE_PIXELS = 1            # 墙体膨胀
MIN_COMPONENT = 8            # 连通域少于 N 格 → 删除


def main():
    parser = argparse.ArgumentParser(description='PCD → 2D Map')
    parser.add_argument('input', help='输入 PCD 文件')
    parser.add_argument('--output', default='2D_map', help='输出文件名前缀')
    args = parser.parse_args()

    # ── 1. 读取 PCD ──────────────────────────────────
    import open3d as o3d
    print(f'📂 读取 {args.input} ...')
    pcd = o3d.io.read_point_cloud(args.input)
    pts = np.asarray(pcd.points)
    n_total = pts.shape[0]
    print(f'   总点数: {n_total}')

    # 过滤 NaN
    pts = pts[~np.isnan(pts).any(axis=1)]
    print(f'   有效点: {pts.shape[0]}')

    # ── 2. 距离过滤 ──────────────────────────────────
    dist = np.sqrt(pts[:, 0]**2 + pts[:, 1]**2 + pts[:, 2]**2)
    pts = pts[(dist > BLIND_RADIUS) & (dist < MAX_RANGE)]
    print(f'   距离过滤后: {pts.shape[0]}')

    # ── 3. 地面估计 ──────────────────────────────────
    # 取最低 GROUND_PERCENTILE% 的 Z 值中位数
    z_sorted = np.sort(pts[:, 2])
    n_ground = max(100, n_total * GROUND_PERCENTILE // 100)
    ground_z = np.median(z_sorted[:n_ground])
    print(f'   估计地面高度: {ground_z:.3f}m (取最低 %d 个点的中位数)' % n_ground)

    # ── 4. 障碍 / 地面分类 ──────────────────────────
    rel_h = pts[:, 2] - ground_z
    ground_mask = np.abs(rel_h) <= GROUND_TOLERANCE
    obstacle_mask = (rel_h > OBSTACLE_MIN_H) & (rel_h < OBSTACLE_MAX_H)

    gnd_pts = pts[ground_mask]
    obs_pts = pts[obstacle_mask]
    print(f'   地面点: {gnd_pts.shape[0]},  障碍候选点: {obs_pts.shape[0]}')

    # ── 5. 体素降采样 ────────────────────────────────
    def voxel_down(p, sz=0.02):
        if p.shape[0] < 100:
            return p
        idx = np.floor(p[:, :3] / sz).astype(np.int64)
        _, u = np.unique(idx, axis=0, return_index=True)
        return p[u]

    obs_pts = voxel_down(obs_pts, MAP_RESOLUTION)
    print(f'   障碍降采样后: {obs_pts.shape[0]}')

    # ── 6. 投影到 2D 栅格 ────────────────────────────
    # 自动确定地图范围
    margin = 2.0  # 留白 2m
    min_x = np.floor((obs_pts[:, 0].min() - margin) / MAP_RESOLUTION) * MAP_RESOLUTION
    max_x = np.ceil((obs_pts[:, 0].max() + margin) / MAP_RESOLUTION) * MAP_RESOLUTION
    min_y = np.floor((obs_pts[:, 1].min() - margin) / MAP_RESOLUTION) * MAP_RESOLUTION
    max_y = np.ceil((obs_pts[:, 1].max() + margin) / MAP_RESOLUTION) * MAP_RESOLUTION

    W = int((max_x - min_x) / MAP_RESOLUTION)
    H = int((max_y - min_y) / MAP_RESOLUTION)
    print(f'   地图范围: X[{min_x:.1f}, {max_x:.1f}] Y[{min_y:.1f}, {max_y:.1f}]')
    print(f'   栅格尺寸: {W} x {H}')

    # 投影障碍: 计数每个格子里有几个点
    ogx = np.floor((obs_pts[:, 0] - min_x) / MAP_RESOLUTION).astype(np.int32)
    ogy = np.floor((obs_pts[:, 1] - min_y) / MAP_RESOLUTION).astype(np.int32)
    ok = (ogx >= 0) & (ogx < W) & (ogy >= 0) & (ogy < H)
    ogx, ogy = ogx[ok], ogy[ok]

    cnt = np.zeros((H, W), dtype=np.int32)
    np.add.at(cnt, (ogy, ogx), 1)

    # 占据栅格: 格内点数 >= MIN_OBS_POINTS → obstacle
    occ_grid = (cnt >= MIN_OBS_POINTS)

    # ── 7. 后处理 ────────────────────────────────────
    from scipy.ndimage import label, binary_dilation, binary_fill_holes

    # 删除太小的连通域
    lbl, nf = label(occ_grid)
    for i in range(1, nf + 1):
        if np.sum(lbl == i) < MIN_COMPONENT:
            occ_grid[lbl == i] = False

    # 形态学膨胀 (让断墙连接)
    if DILATE_PIXELS > 0:
        occ_grid = binary_dilation(occ_grid,
                                   structure=np.ones((3, 3)),
                                   iterations=DILATE_PIXELS)

    # ── 8. 输出 PGM ──────────────────────────────────
    out_dir = os.path.join(os.path.dirname(__file__), 'maps')
    os.makedirs(out_dir, exist_ok=True)

    # flip Y: PGM 坐标系 Y 向下
    pgm = np.full((H, W), 205, dtype=np.uint8)  # unknown = 205
    pgm[occ_grid] = 0  # occupied = 0 (black)

    pgm_flip = np.flipud(pgm)

    pgm_path = os.path.join(out_dir, f'{args.output}.pgm')
    with open(pgm_path, 'wb') as f:
        f.write(f'P5\n{W} {H}\n255\n'.encode())
        f.write(pgm_flip.tobytes())
    print(f'   ✅ PGM 已保存: {pgm_path}')

    # ── 9. 输出 YAML ─────────────────────────────────
    yaml_path = os.path.join(out_dir, f'{args.output}.yaml')
    with open(yaml_path, 'w') as f:
        f.write(f'image: {args.output}.pgm\n')
        f.write(f'mode: trinary\n')
        f.write(f'resolution: {MAP_RESOLUTION}\n')
        f.write(f'origin: [{min_x}, {min_y}, 0.0]\n')
        f.write(f'negate: 0\n')
        f.write(f'occupied_thresh: 0.65\n')
        f.write(f'free_thresh: 0.25\n')
    print(f'   ✅ YAML 已保存: {yaml_path}')

    # ── 10. 输出 Debug PNG ───────────────────────────
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # 全部点云 (按高度着色)
        ax = axes[0]
        sample = np.random.choice(pts.shape[0], min(50000, pts.shape[0]), replace=False)
        sc = ax.scatter(pts[sample, 0], pts[sample, 1], c=pts[sample, 2],
                         s=0.5, cmap='jet', alpha=0.7)
        ax.set_title(f'All Points (Z-colored, {pts.shape[0]} pts)')
        ax.set_aspect('equal')
        plt.colorbar(sc, ax=ax, label='Z (m)')

        # 障碍 + 地面
        ax = axes[1]
        s_obs = np.random.choice(obs_pts.shape[0], min(20000, obs_pts.shape[0]), replace=False)
        s_gnd = np.random.choice(gnd_pts.shape[0], min(20000, gnd_pts.shape[0]), replace=False)
        ax.scatter(gnd_pts[s_gnd, 0], gnd_pts[s_gnd, 1], c='green', s=0.5, alpha=0.5, label=f'Ground ({gnd_pts.shape[0]})')
        ax.scatter(obs_pts[s_obs, 0], obs_pts[s_obs, 1], c='red', s=0.5, alpha=0.7, label=f'Obstacle ({obs_pts.shape[0]})')
        ax.legend(markerscale=20)
        ax.set_title('Classification: Red=Obstacle, Green=Ground')
        ax.set_aspect('equal')

        # 最终 2D 栅格
        ax = axes[2]
        rgb = np.zeros((H, W, 3), dtype=np.uint8)
        rgb[:, :, 0] = 128  # unknown → gray
        rgb[:, :, 1] = 128
        rgb[:, :, 2] = 128
        rgb[occ_grid] = [0, 0, 0]  # obstacle → black
        # 地面格也标出来
        ggx = np.floor((gnd_pts[:, 0] - min_x) / MAP_RESOLUTION).astype(np.int32)
        ggy = np.floor((gnd_pts[:, 1] - min_y) / MAP_RESOLUTION).astype(np.int32)
        gok = (ggx >= 0) & (ggx < W) & (ggy >= 0) & (ggy < H)
        for gx, gy in zip(ggx[gok], ggy[gok]):
            if not occ_grid[gy, gx]:
                rgb[gy, gx] = [0, 255, 0]  # ground → green

        ax.imshow(rgb, origin='lower',
                  extent=[min_x, max_x, min_y, max_y])
        ax.set_title(f'2D Map: {np.sum(occ_grid)} occupied cells')
        ax.set_aspect('equal')

        plt.tight_layout()
        png_path = os.path.join(out_dir, f'{args.output}_debug.png')
        plt.savefig(png_path, dpi=150)
        plt.close()
        print(f'   ✅ Debug PNG 已保存: {png_path}')
    except Exception as e:
        print(f'   ⚠️  Debug PNG 失败: {e}')

    # ── 统计 ─────────────────────────────────────────
    area = np.sum(occ_grid) * MAP_RESOLUTION * MAP_RESOLUTION
    print(f'\n📊 结果: {np.sum(occ_grid)} occupied cells ≈ {area:.1f} m² 墙壁')
    print(f'   地图尺寸: {W*MAP_RESOLUTION:.1f}m x {H*MAP_RESOLUTION:.1f}m')
    print(f'   文件: {pgm_path}')
    print(f'         {yaml_path}')


if __name__ == '__main__':
    main()
