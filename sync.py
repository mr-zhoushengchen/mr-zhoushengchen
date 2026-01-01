# -*- coding: utf-8 -*-
import os, requests, re, shutil
from collections import defaultdict

TOKEN = os.environ.get('G_T')
REPO = "miss-shiyi/miss-shiyi"

def sync():
    # 1. 初始化目录
    backup_dir = "BACKUP"
    wiki_temp = "wiki_temp"
    for d in [backup_dir, wiki_temp]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    headers = {"Authorization": f"token {TOKEN}"}
    all_issues = []
    page = 1

    # 2. 全量分页获取 Issue (解决 24418 条及更多的限制问题)
    print("正在从 GitHub API 获取全量 Issue...")
    while True:
        url = f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        issues = response.json()
        if not issues or not isinstance(issues, list): break
        all_issues.extend(issues)
        if len(issues) < 100: break
        page += 1

    categories = defaultdict(list)

    # 3. 处理每一篇内容
    for issue in all_issues:
        if "pull_request" in issue: continue
        
        labels = [l['name'] for l in issue['labels']]
        cat = labels[0] if labels else "未分类"
        date = issue['created_at'].split('T')[0]
        
        # 清洗标题，移除系统非法字符
        clean_title = re.sub(r'[\/\\:\*\?"<>\|]', '', issue['title']).strip().replace(" ", "-")
        
        # A. 主仓库物理备份 (BACKUP/分类/日期-标题.md)
        cat_dir = os.path.join(backup_dir, cat)
        if not os.path.exists(cat_dir): os.makedirs(cat_dir)
        main_file_name = f"{date}-{clean_title}.md"
        with open(os.path.join(cat_dir, main_file_name), "w", encoding="utf-8") as f:
            f.write(f"# {issue['title']}\n\n{issue['body'] or ''}")

        # B. Wiki 备份 (扁平化命名)
        wiki_file_name = f"[{cat}] {date}-{clean_title}.md"
        with open(os.path.join(wiki_temp, wiki_file_name), "w", encoding="utf-8") as f:
            f.write(f"# {issue['title']}\n\n> 分类: {cat} | 日期: {date}\n\n---\n\n{issue['body'] or ''}")

        # C. 记录列表链接 (指向主仓库)
        rel_path = f"BACKUP/{cat}/{main_file_name}".replace(" ", "%20")
        categories[cat].append(f"- [{issue['title']}]({rel_path}) — `{date}`")

    # 4. 生成 README.md (带折叠逻辑)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# 周生辰纲\n\n")
        f.write(f"> [📖 点击进入 Wiki 沉浸阅读](https://github.com/{REPO}/wiki)\n\n")
        f.write(f"目前共计 **{len(all_issues)}** 篇文章，已分类归档：\n\n---\n\n")

        for cat_name in sorted(categories.keys()):
            posts = categories[cat_name]
            f.write(f"### 📁 {cat_name} ({len(posts)})\n")
            
            # 展示最新的 5 条
            visible = posts[:5]
            f.write("\n".join(visible) + "\n")
            
            # 超过 5 条则折叠
            if len(posts) > 5:
                hidden = posts[5:]
                f.write("\n<details>\n")
                f.write(f"<summary>展开查看更多 ({len(hidden)} 篇)</summary>\n\n")
                f.write("\n".join(hidden) + "\n")
                f.write("\n</details>\n")
            f.write("\n")

        f.write("---\n*最后全量更新: {issues[0]['updated_at'] if all_issues else 'N/A'}*")

    # 5. 生成 index.md 和 .nojekyll (确保 GitHub Pages 渲染)
    with open("index.md", "w", encoding="utf-8") as f:
        f.write("---\nlayout: default\ntitle: 拾遗集\n---\n\n")
        with open("README.md", "r", encoding="utf-8") as r:
            f.write(r.read())
    
    open(".nojekyll", "w").close()

    print(f"✅ 处理成功: 已同步 {len(all_issues)} 篇文章")

if __name__ == "__main__":
    sync()
