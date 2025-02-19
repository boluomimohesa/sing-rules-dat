import json
import argparse
import os
import sys

def remove_duplicates(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{input_file}'. 请确保文件路径正确。", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 无法解析 JSON 文件 '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    
    seen_domains = set()
    seen_suffixes = set()
    seen_keywords = set()
    
    new_rules = []
    for rule in data.get("rules", []):
        new_rule = {}
        
        # 处理 domain
        domain = rule.get("domain")
        if isinstance(domain, list):
            unique_domain = []
            for d in domain:
                if d not in seen_domains:
                    seen_domains.add(d)
                    unique_domain.append(d)
            if unique_domain:
                new_rule["domain"] = unique_domain
        elif isinstance(domain, str):
            if domain not in seen_domains:
                seen_domains.add(domain)
                new_rule["domain"] = domain
        
        # 处理 domain_suffix
        domain_suffix = rule.get("domain_suffix")
        if isinstance(domain_suffix, list):
            unique_suffix = []
            for s in domain_suffix:
                if s not in seen_suffixes:
                    seen_suffixes.add(s)
                    unique_suffix.append(s)
            if unique_suffix:
                new_rule["domain_suffix"] = unique_suffix
        elif isinstance(domain_suffix, str):
            if domain_suffix not in seen_suffixes:
                seen_suffixes.add(domain_suffix)
                new_rule["domain_suffix"] = domain_suffix
        
        # 处理 domain_keyword
        domain_keyword = rule.get("domain_keyword")
        if isinstance(domain_keyword, list):
            unique_keyword = []
            for k in domain_keyword:
                if k not in seen_keywords:
                    seen_keywords.add(k)
                    unique_keyword.append(k)
            if unique_keyword:
                new_rule["domain_keyword"] = unique_keyword
        elif isinstance(domain_keyword, str):
            if domain_keyword not in seen_keywords:
                seen_keywords.add(domain_keyword)
                new_rule["domain_keyword"] = domain_keyword
        
        # 如果新规则有任何字段，则添加到新规则列表中
        if new_rule:
            new_rules.append(new_rule)
    
    data["rules"] = new_rules
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"去重完成，结果已保存到 '{output_file}'")
    except IOError as e:
        print(f"错误: 无法写入文件 '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="去除 JSON 文件中跨规则的重复内容。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage="python deduplicate_json.py --data input.json --output output.json"
    )
    parser.add_argument(
        '--data', '-d',
        required=True,
        help="输入的 JSON 文件路径"
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help="输出的 JSON 文件路径"
    )
    args = parser.parse_args()

    input_file = args.data
    output_file = args.output

    # 检查输入文件是否存在
    if not os.path.isfile(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在。", file=sys.stderr)
        sys.exit(1)

    remove_duplicates(input_file, output_file)

if __name__ == "__main__":
    main()