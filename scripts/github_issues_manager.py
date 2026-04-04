#!/usr/bin/env python3
"""
github_issues_manager.py - GitHub Issues 自动化管理

能力：
1. 创建任务 Issue（含编号/负责人/完成标准）
2. 更新 Issue 状态（进行中/完成/卡住）
3. 关闭 Issue 并归档结果
4. 与 auto_evolve_hook.py 联动，任务完成自动关闭 Issue

用法：
    python scripts/github_issues_manager.py create --task-id T09 --title "任务标题" --repo owner/repo
    python scripts/github_issues_manager.py update --issue 1 --status done --repo owner/repo
    python scripts/github_issues_manager.py close --issue 1 --result "完成内容" --repo owner/repo
"""

import argparse
import subprocess
import sys
import json
from datetime import datetime


def run_gh(args: list) -> tuple[int, str]:
    """执行 gh 命令，返回 (exit_code, output)"""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip() or result.stderr.strip()


def create_issue(task_id: str, title: str, repo: str, assignee: str = "@me",
                 body: str = None) -> int:
    """创建 GitHub Issue，返回 Issue 编号"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    default_body = f"""**任务编号：** {task_id}
**负责人：** 组长
**创建时间：** {now}

**任务描述：**
{body or title}

**完成标准：**
- [ ] 代码已提交并通过测试
- [ ] exit code = 0 已确认
- [ ] GitHub + Gitee 已同步"""

    code, out = run_gh([
        "issue", "create",
        "--repo", repo,
        "--title", f"{task_id}：{title}",
        "--body", default_body,
        "--label", "待处理",
        "--assignee", assignee
    ])

    if code != 0:
        print(f"[ERROR] 创建 Issue 失败 (exit {code}): {out}")
        return -1

    # 解析 Issue 编号
    issue_url = out.strip()
    issue_num = int(issue_url.split("/")[-1])
    print(f"[OK] Issue #{issue_num} 创建成功: {issue_url}")
    return issue_num


def update_status(issue_num: int, repo: str, status: str, comment: str = None):
    """更新 Issue 状态标签"""
    label_map = {
        "start": ("待处理", "进行中"),
        "done": ("进行中", "已完成"),
        "stuck": ("进行中", "卡住"),
    }

    if status in label_map:
        remove_label, add_label = label_map[status]
        run_gh(["issue", "edit", str(issue_num), "--repo", repo,
                "--remove-label", remove_label, "--add-label", add_label])

    if comment:
        code, out = run_gh(["issue", "comment", str(issue_num),
                            "--repo", repo, "--body", comment])
        if code == 0:
            print(f"[OK] Issue #{issue_num} 已更新状态: {status}")
        else:
            print(f"[ERROR] 评论失败: {out}")


def close_issue(issue_num: int, repo: str, result: str):
    """关闭 Issue 并记录结果"""
    comment = f"✅ 任务完成\n\n**结果：** {result}\n\n**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run_gh(["issue", "comment", str(issue_num), "--repo", repo, "--body", comment])
    code, out = run_gh(["issue", "close", str(issue_num), "--repo", repo])
    if code == 0:
        print(f"[OK] Issue #{issue_num} 已关闭")
    else:
        print(f"[ERROR] 关闭失败 (exit {code}): {out}")


def list_issues(repo: str, label: str = "进行中"):
    """列出当前状态的 Issues"""
    code, out = run_gh([
        "issue", "list", "--repo", repo,
        "--label", label,
        "--json", "number,title,assignees,createdAt",
        "--jq", '.[] | "[#\(.number)] \(.title)"'
    ])
    if code == 0 and out:
        print(f"\n📋 {label} 任务列表：")
        for line in out.split("\n"):
            print(f"  {line}")
    else:
        print(f"[INFO] 无 {label} 任务")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Issues 自动化管理")
    subparsers = parser.add_subparsers(dest="command")

    # create
    p_create = subparsers.add_parser("create", help="创建 Issue")
    p_create.add_argument("--task-id", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--repo", required=True)
    p_create.add_argument("--body", default=None)
    p_create.add_argument("--assignee", default="@me")

    # update
    p_update = subparsers.add_parser("update", help="更新 Issue 状态")
    p_update.add_argument("--issue", type=int, required=True)
    p_update.add_argument("--status", required=True, choices=["start", "done", "stuck"])
    p_update.add_argument("--repo", required=True)
    p_update.add_argument("--comment", default=None)

    # close
    p_close = subparsers.add_parser("close", help="关闭 Issue")
    p_close.add_argument("--issue", type=int, required=True)
    p_close.add_argument("--repo", required=True)
    p_close.add_argument("--result", required=True)

    # list
    p_list = subparsers.add_parser("list", help="列出 Issues")
    p_list.add_argument("--repo", required=True)
    p_list.add_argument("--label", default="进行中")

    args = parser.parse_args()

    if args.command == "create":
        create_issue(args.task_id, args.title, args.repo, args.assignee, args.body)
    elif args.command == "update":
        update_status(args.issue, args.repo, args.status, args.comment)
    elif args.command == "close":
        close_issue(args.issue, args.repo, args.result)
    elif args.command == "list":
        list_issues(args.repo, args.label)
    else:
        parser.print_help()
