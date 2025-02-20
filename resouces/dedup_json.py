#!/usr/bin/env python3

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Union, Any, Set
import logging
import argparse
import sys

# 脚本版本号
__version__ = "1.0.3"  # 更新版本号以反映新功能

# 定义字段值类型
FieldValue = Union[str, List[str]]
Rule = Dict[str, FieldValue]

def setup_logging(enable_file_log: bool) -> None:
    """配置日志记录：命令行始终输出，可选写入文件"""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    if enable_file_log:
        file_handler = logging.FileHandler("deduplication.log", mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logging.info("日志文件记录已启用")
    else:
        logging.info("日志文件记录已禁用")

def backup_file(input_file: str, enable_backup: bool) -> str | None:
    """备份输入文件到 backups 目录，带日期时间戳"""
    if not enable_backup:
        logging.info("用户已禁用备份")
        return None
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = f"{backup_dir}/{os.path.basename(input_file)}.backup_{timestamp}"
    shutil.copy2(input_file, backup_path)
    logging.info(f"创建备份文件: {backup_path}")
    return backup_path

def deduplicate_list_field(rule: Rule, global_seen: Set[str]) -> None:
    """对规则中的列表字段去重，并跨字段与全局去重"""
    for key in ["domain", "domain_suffix", "domain_keyword"]:
        if key in rule:
            value = rule[key]
            if isinstance(value, str):
                if value in global_seen:
                    del rule[key]
                    logging.info(f"移除规则中全局重复的 '{key}': {value}")
                else:
                    global_seen.add(value)
            elif isinstance(value, list):
                original = value.copy()
                rule[key] = list(dict.fromkeys(v for v in value if v not in global_seen))
                global_seen.update(rule[key])
                if original != rule[key]:
                    logging.info(f"字段 '{key}' 在规则中去重: {json.dumps(rule)}")

def get_field_value_as_set(value: FieldValue) -> Set[str]:
    """将字段值转换为集合，便于比较"""
    return {value} if isinstance(value, str) else set(value) if isinstance(value, list) else set()

def is_single_field_rule(rule: Rule) -> tuple[bool, str, str]:
    """检查规则是否只有一个非空字段，并返回字段名和值"""
    non_empty_fields = {
        key: value for key, value in rule.items()
        if value and (isinstance(value, str) or (isinstance(value, list) and value))
    }
    if len(non_empty_fields) == 1:
        key, value = next(iter(non_empty_fields.items()))
        if isinstance(value, str) or (isinstance(value, list) and len(value) == 1):
            return True, key, value[0] if isinstance(value, list) else value
    return False, "", ""

def process_json(input_file: str, output_file: str, enable_backup: bool, enable_write: bool) -> None:
    """主处理函数：去重并输出结果"""
    backup_path = backup_file(input_file, enable_backup)

    with open(input_file, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    rules: List[Rule] = data.get("rules", [])
    logging.info(f"从 {input_file} 加载了 {len(rules)} 条规则")

    # 全局去重集合
    global_seen: Set[str] = set()

    # 第一步：字段内和全局去重
    for i, rule in enumerate(rules):
        deduplicate_list_field(rule, global_seen)

    # 第二步：删除单字段重复规则（默认启用）
    rules_to_remove: Set[int] = set()
    for i, rule in enumerate(rules):
        is_single, field_name, value = is_single_field_rule(rule)
        if is_single and value in global_seen:
            rules_to_remove.add(i)
            logging.info(f"标记规则以删除: {json.dumps(rule)} (全局重复值 '{value}' 在 '{field_name}')")
    
    for idx in sorted(rules_to_remove, reverse=True):
        removed_rule = rules.pop(idx)
        logging.info(f"已删除规则: {json.dumps(removed_rule)}")

    # 更新数据
    data["rules"] = rules
    logging.info(f"处理后剩余 {len(rules)} 条规则")

    # 根据 --write 选项决定输出文件
    target_file = input_file if enable_write else output_file
    if enable_write and ("--output" in sys.argv or "-o" in sys.argv):
        logging.warning("已启用 --write 选项，--output 选项将被忽略，结果将直接写入输入文件")

    os.makedirs(os.path.dirname(target_file) or ".", exist_ok=True)
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info(f"已将处理结果写入 {target_file}")

def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="对 JSON 规则进行去重，支持高级选项。",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="input.json",
        help="输入 JSON 文件路径（默认: input.json）"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output.json",
        help="输出 JSON 文件路径（默认: output.json，启用 --write 时失效）"
    )
    parser.add_argument(
        "--log",
        # type=lambda x: x.lower() == "true",
        # store_true 只检查 --log 是否在命令行中出现
        action="store_true",
        default=False,
        help="启用/禁用日志文件记录 (true/false，默认: true，命令行输出不受影响)"
    )
    parser.add_argument(
        "--bak",
        type=lambda x: x.lower() == "true",
        default=True,
        help="启用/禁用备份 (true/false，默认: true)"
    )
    parser.add_argument(
        "--write", "-w",
        action="store_true",
        help="直接将结果写入输入文件（启用时 --output 失效）"
    )
    parser.add_argument(
        "--help", "-h",
        action="help",
        help="显示此帮助信息并退出"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"dedup_json {__version__}",
        help="显示脚本版本号并退出"
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    return parser.parse_args()

def main() -> None:
    """主函数"""
    args = parse_arguments()
    setup_logging(args.log)
    
    if not os.path.exists(args.file):
        logging.error(f"输入文件 {args.file} 不存在")
        raise FileNotFoundError(f"输入文件 {args.file} 不存在")
    
    try:
        process_json(args.file, args.output, args.bak, args.write)
        logging.info("处理成功完成")
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()