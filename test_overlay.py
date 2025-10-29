"""
测试眼动轨迹 Overlay 功能

用法:
    python test_overlay.py --video <video_path> --edf <edf_path> [--output <output_path>]

示例:
    python test_overlay.py --video test.mp4 --edf example.edf
    python test_overlay.py --video test.mp4 --edf example.edf --output result_gaze.mp4
"""

import argparse
import logging
from pathlib import Path
from screen_recorder import overlay_gaze_on_video

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="测试眼动轨迹叠加到视频的功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python test_overlay.py --video test.mp4 --edf example.edf
  python test_overlay.py --video recordings/test.mp4 --edf eyelink_data/example.edf --output test_result.mp4
  python test_overlay.py -v test.mp4 -e example.edf -o output.mp4 --color 255,0,0 --radius 30
        """
    )
    
    parser.add_argument(
        "-v", "--video",
        required=True,
        help="输入视频文件路径"
    )
    
    parser.add_argument(
        "-e", "--edf",
        required=True,
        help="EDF 眼动数据文件路径"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="输出视频文件路径（默认：在输入视频同目录下生成 <name>_gaze.mp4）"
    )
    
    parser.add_argument(
        "--color",
        default="0,255,0",
        help="注视点颜色 (B,G,R 格式，默认：0,255,0 即绿色)"
    )
    
    parser.add_argument(
        "--radius",
        type=int,
        default=20,
        help="注视点半径（像素，默认：20）"
    )
    
    args = parser.parse_args()
    
    # 检查文件存在性
    video_path = Path(args.video)
    edf_path = Path(args.edf)
    
    if not video_path.exists():
        logger.error(f"视频文件不存在: {video_path}")
        return 1
    
    if not edf_path.exists():
        logger.error(f"EDF 文件不存在: {edf_path}")
        return 1
    
    # 解析颜色
    try:
        color_parts = [int(x.strip()) for x in args.color.split(",")]
        if len(color_parts) != 3:
            raise ValueError("颜色必须是 3 个值")
        gaze_color = tuple(color_parts)
    except Exception as e:
        logger.error(f"颜色格式错误: {args.color}，应为 'B,G,R' 格式，例如 '0,255,0'")
        return 1
    
    # 输出路径
    if args.output:
        output_path = args.output
    else:
        output_path = str(video_path.with_name(video_path.stem + "_gaze.mp4"))
    
    # 显示配置
    logger.info("=" * 60)
    logger.info("测试 Overlay 功能")
    logger.info("=" * 60)
    logger.info(f"视频文件: {video_path}")
    logger.info(f"EDF 文件: {edf_path}")
    logger.info(f"输出文件: {output_path}")
    logger.info(f"注视点颜色: {gaze_color} (B,G,R)")
    logger.info(f"注视点半径: {args.radius} 像素")
    logger.info("=" * 60)
    
    # 执行 overlay
    try:
        success = overlay_gaze_on_video(
            video_path=str(video_path),
            edf_path=str(edf_path),
            output_path=output_path,
            gaze_color=gaze_color,
            gaze_radius=args.radius
        )
        
        if success:
            logger.info("=" * 60)
            logger.info("✅ Overlay 成功完成！")
            logger.info(f"输出文件: {output_path}")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("❌ Overlay 失败")
            return 1
            
    except Exception as e:
        logger.exception(f"执行 overlay 时出错: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


