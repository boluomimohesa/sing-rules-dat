#!/bin/bash

# 检查是否提供了目录参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <目录路径>"
    exit 1
fi

# 获取目录路径
directory="$1"

# 检查目录是否存在
if [ ! -d "$directory" ]; then
    echo "错误: 目录 '$directory' 不存在"
    exit 1
fi

# 计数器
processed_files=0
modified_files=0

# 遍历目录中的所有文件
find "$directory" -type f | while read -r file; do
    processed_files=$((processed_files + 1))
    
    # 检查文件是否以 "domain:" 开头
    if grep -q "^domain:" "$file"; then
        # 创建临时文件
        temp_file=$(mktemp)
        
        # 使用 sed 去除文件开头的 "domain:"
        sed 's/^domain://' "$file" > "$temp_file"
        
        # 将临时文件内容移回原文件
        mv "$temp_file" "$file"
        
        echo "已修改: $file"
        modified_files=$((modified_files + 1))
    fi
done

echo "处理完成! 共处理 $processed_files 个文件，修改了 $modified_files 个文件。"
