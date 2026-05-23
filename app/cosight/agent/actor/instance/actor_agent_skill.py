# Copyright 2025 ZTE Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from app.agent_dispatcher.infrastructure.entity.SkillFunction import SkillFunction
from config import mcp_server_config_dir
from app.common.domain.util.json_util import JsonUtil


def execute_code_skill(work_space_path):
    return {
        'skill_name': 'execute_code',
        'skill_type': "function",
        'display_name_zh': '执行代码',
        'display_name_en': 'Execute Code',
        'description_zh': f'执行给定的代码片段并返回结果,若要处理本地文件，必须在工作区: {work_space_path or os.getenv("WORKSPACE_PATH") or os.getcwd()}',
        'description_en': f'Execute a given code snippet and return the result. To process the local file, it must be in the working area: {work_space_path or os.getenv("WORKSPACE_PATH") or os.getcwd()}',
        'semantic_apis': ["api_code_execution"],
        'function': SkillFunction(
            id='4c44f9ad-be5c-4e6c-a9d8-1426b23828a9',
            name='app.cosight.code_interpreter.execute_code',
            description_zh='执行Python代码片段并返回输出结果',
            description_en='Execute Python code snippet and return the output',
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description_zh": "要执行的Python代码",
                        "description_en": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        )
    }


def search_google_skill():
    return {
        'skill_name': 'search_google',
        'skill_type': "function",
        'display_name_zh': '谷歌搜索',
        'display_name_en': 'Google Search',
        'description_zh': '使用谷歌搜索引擎搜索给定查询的信息',
        'description_en': 'Use Google search engine to search information for the given query',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='3c44f9ad-be5c-4e6c-a9d8-1426b23828a0',
            name='app.cosight.search_toolkit.search_google',
            description_zh='通过谷歌搜索引擎获取查询结果',
            description_en='Get search results using Google search engine',
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["query"]
            }
        )
    }


def tavily_search_skill():
    return {
        'skill_name': 'tavily_search',
        'skill_type': "function",
        'display_name_zh': 'Tavily搜索',
        'display_name_en': 'Tavily Search',
        'description_zh': '使用Tavily搜索引擎搜索给定查询的信息',
        'description_en': 'Use Tavily search engine to search information for the given query',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='3c44f9ad-be5c-4e6c-a9d8-1426b23828a0',
            name='app.cosight.search_toolkit.search_google',
            description_zh='通过谷歌搜索引擎获取查询结果',
            description_en='Get search results using Tavily search engine',
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["query"]
            }
        )
    }


def search_duckgo_skill():
    return {
        'skill_name': 'search_duckgo',
        'skill_type': "function",
        'display_name_zh': 'DuckDuckGo搜索',
        'display_name_en': 'Google Search',
        'description_zh': '使用DuckDuckGo搜索引擎搜索给定查询的信息',
        'description_en': 'Use DuckDuckGo search engine to search information for the given query',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='3c44f9ad-be5c-4e6c-a9d8-1426b23828a0',
            name='app.cosight.search_toolkit.search_google',
            description_zh='使用DuckDuckGo搜索引擎搜索给定查询的信息',
            description_en='Get search results using DuckDuckGo search engine',
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    },
                    "source": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容类型，例如：text，images，videos",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["query"]
            }
        )
    }


def search_wiki_skill():
    return {
        'skill_name': 'search_wiki',
        'skill_type': "function",
        'display_name_zh': '维基百科搜索',
        'display_name_en': 'Google Search',
        'description_zh': '使用维基百科搜索工具搜索给定查询的信息',
        'description_en': 'Use wiki search engine to search information for the given query',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='3c44f9ad-be5c-4e6c-a9d8-1426b23828a0',
            name='app.cosight.tool.search_toolkit.search_wiki',
            description_zh='使用维基百科搜索工具搜索给定查询的信息（仅摘要，不含编辑历史）',
            description_en='Get Wikipedia article summary only (no revision history)',
            parameters={
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["entity"]
            }
        )
    }


def _wikipedia_tool_skill(skill_name, display_zh, display_en, desc_zh, desc_en, properties, required):
    return {
        'skill_name': skill_name,
        'skill_type': "function",
        'display_name_zh': display_zh,
        'display_name_en': display_en,
        'description_zh': desc_zh,
        'description_en': desc_en,
        'semantic_apis': ["api_wikipedia"],
        'function': SkillFunction(
            id=f'wiki-{skill_name}',
            name=f'app.cosight.tool.wikipedia_revision_toolkit.WikipediaRevisionToolkit',
            description_zh=desc_zh,
            description_en=desc_en,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
            }
        )
    }


def wikipedia_revision_skills():
    title_prop = {
        "title": {
            "type": "string",
            "description_zh": "维基百科页面标题，如 ZTE 或 ZTE Corporation",
            "description_en": "Wikipedia page title, e.g. ZTE or ZTE Corporation",
        }
    }
    return [
        _wikipedia_tool_skill(
            "count_wikipedia_edits_in_year",
            "维基编辑次数统计",
            "Wikipedia edit count",
            "统计某页面在指定日历年内的编辑次数（MediaWiki API，程序计数）",
            "Count edits to a Wikipedia page in a calendar year via MediaWiki API",
            {**title_prop, "year": {"type": "integer", "description_zh": "年份，如 2025", "description_en": "Year e.g. 2025"}},
            ["title", "year"],
        ),
        _wikipedia_tool_skill(
            "get_wikipedia_revisions",
            "维基修订列表",
            "Wikipedia revisions",
            "获取页面在时间范围内的修订元数据列表",
            "List revision metadata for a page in a time range",
            {
                **title_prop,
                "start": {"type": "string", "description_en": "ISO start time e.g. 2025-01-01T00:00:00Z"},
                "end": {"type": "string", "description_en": "ISO end time e.g. 2025-12-31T23:59:59Z"},
            },
            ["title", "start", "end"],
        ),
        _wikipedia_tool_skill(
            "compute_wikipedia_reference_delta",
            "维基引用数差值",
            "Wikipedia reference delta",
            "计算两年首个修订版本之间 reference 数量差值",
            "Reference count delta between first revisions in two years",
            {
                **title_prop,
                "year_a": {"type": "integer"},
                "year_b": {"type": "integer"},
            },
            ["title", "year_a", "year_b"],
        ),
        _wikipedia_tool_skill(
            "find_wikipedia_revision_by_size_delta",
            "按字节增量找修订",
            "Find revision by size delta",
            "在指定年份找到相对父修订 size 增加恰好为 target_delta 的编辑",
            "Find revision in year whose size increase equals target_delta",
            {
                **title_prop,
                "year": {"type": "integer"},
                "target_delta": {"type": "integer", "description_en": "Exact size increase in bytes"},
            },
            ["title", "year", "target_delta"],
        ),
        _wikipedia_tool_skill(
            "extract_section_from_revision",
            "提取历史版本章节",
            "Extract section from revision",
            "从指定 oldid 的维基文本中只提取一个章节（如 Subsidiaries）",
            "Extract one wikitext section from a revision by revid",
            {
                "revid": {"type": "integer"},
                "section_title": {"type": "string"},
            },
            ["revid", "section_title"],
        ),
        _wikipedia_tool_skill(
            "count_references_for_revision",
            "统计修订引用数",
            "Count references in revision",
            "程序统计某修订版本 wikitext 中 <ref> 数量",
            "Programmatic <ref> count for a revision",
            {"revid": {"type": "integer"}},
            ["revid"],
        ),
        _wikipedia_tool_skill(
            "get_wikipedia_revision_before_date",
            "指定日期前的维基修订",
            "Wikipedia revision before date",
            "获取某页面在指定 ISO 时间之前的最新修订版本",
            "Latest Wikipedia revision strictly before an ISO timestamp",
            {
                **title_prop,
                "before": {
                    "type": "string",
                    "description_en": "ISO timestamp upper bound e.g. 2023-08-01T00:00:00Z",
                },
            },
            ["title", "before"],
        ),
    ]


def _contest_tool_skill(skill_name, display_zh, display_en, desc_zh, desc_en, properties, required, api_tag="api_contest"):
    return {
        'skill_name': skill_name,
        'skill_type': "function",
        'display_name_zh': display_zh,
        'display_name_en': display_en,
        'description_zh': desc_zh,
        'description_en': desc_en,
        'semantic_apis': [api_tag],
        'function': SkillFunction(
            id=f'contest-{skill_name}',
            name=f'app.cosight.tool.contest_document_toolkit.ContestDocumentToolkit',
            description_zh=desc_zh,
            description_en=desc_en,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
            }
        )
    }


def contest_document_skills():
    return [
        _contest_tool_skill(
            "lookup_book_publication_year",
            "图书出版年份查询",
            "Book publication year lookup",
            "通过 Open Library / Wikipedia 程序化查询图书首次出版年份",
            "Programmatic book publication year via Open Library or Wikipedia",
            {
                "book_title": {
                    "type": "string",
                    "description_en": "Book title e.g. The Propitious Esculent",
                }
            },
            ["book_title"],
        ),
        _contest_tool_skill(
            "count_term_occurrences",
            "文本词频计数",
            "Count term occurrences",
            "在文本中程序化统计指定词/年份出现次数",
            "Programmatic occurrence count of a term in text",
            {
                "text": {"type": "string"},
                "term": {"type": "string", "description_en": "Term or year to count"},
                "case_sensitive": {"type": "boolean", "default": False},
            },
            ["text", "term"],
        ),
        _contest_tool_skill(
            "extract_abstract_from_text",
            "提取论文摘要",
            "Extract paper abstract",
            "从论文全文中用规则提取 Abstract / Antraste 章节",
            "Extract abstract section from academic paper plain text",
            {"text": {"type": "string"}},
            ["text"],
        ),
        _contest_tool_skill(
            "count_reference_year_in_paper_abstract",
            "摘要中引用书年份计数",
            "Count book year in paper abstract",
            "Q4 管道：查参考书出版年 → 定位论文摘要 → 统计年份出现次数",
            "Q4 pipeline: book year lookup, paper abstract extraction, year count",
            {
                "paper_title": {"type": "string", "description_en": "Paper title"},
                "author": {"type": "string", "description_en": "Author name"},
                "reference_book_title": {"type": "string", "description_en": "Referenced book title"},
                "document_url": {
                    "type": "string",
                    "description_en": "Optional direct PDF/URL if already known",
                    "default": "",
                },
            },
            ["paper_title", "author", "reference_book_title"],
        ),
        _contest_tool_skill(
            "search_book_page_for_text",
            "图书页码检索",
            "Search book page for text",
            "Q10 管道：定位指定版次 PDF → 按关键词搜索页码",
            "Q10 pipeline: find edition PDF and return page number for search phrases",
            {
                "book_title": {"type": "string", "description_en": "Book title e.g. Joy of Cooking"},
                "edition_year": {"type": "integer", "description_en": "Edition year e.g. 1975"},
                "search_phrases": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description_en": "Phrases that must all appear on the page, e.g. raccoon, stuffing",
                },
                "pdf_url": {
                    "type": "string",
                    "description_en": "Optional direct PDF URL",
                    "default": "",
                },
            },
            ["book_title", "edition_year", "search_phrases"],
        ),
    ]


def rail_connection_skills():
    return [
        {
            'skill_name': 'count_train_line_station_connections',
            'skill_type': "function",
            'display_name_zh': '铁路共站线路统计',
            'display_name_en': 'Shared-station rail line count',
            'description_zh': '统计某列车线路各站在指定历史日期与其他通勤/重轨线路的共站连接数（排除地铁/轻轨）',
            'description_en': 'Count distinct commuter/heavy rail lines sharing stations with a train route at a historical date',
            'semantic_apis': ["api_rail"],
            'function': SkillFunction(
                id='rail-count-connections',
                name='app.cosight.tool.rail_connection_toolkit.RailConnectionToolkit',
                description_zh='Q3 管道：维基历史版本解析站点 → 提取共站线路 → 过滤并计数',
                description_en='Q3 pipeline: parse historical Wikipedia route/stations and count connecting rail lines',
                parameters={
                    "type": "object",
                    "properties": {
                        "train_page_title": {
                            "type": "string",
                            "description_en": "Wikipedia train page title e.g. Adirondack (train)",
                        },
                        "as_of_date": {
                            "type": "string",
                            "description_en": "Historical cutoff date YYYY-MM-DD e.g. 2023-07-31",
                        },
                        "exclude_self_line": {
                            "type": "boolean",
                            "description_en": "Exclude the query train line itself",
                            "default": True,
                        },
                    },
                    "required": ["train_page_title", "as_of_date"],
                }
            )
        }
    ]


def search_image_skill():
    return {
        'skill_name': 'image_search',
        'skill_type': "function",
        'display_name_zh': '图片搜索工具',
        'display_name_en': 'Image Search',
        'description_zh': '使用图片搜索工具搜索需要的图片信息',
        'description_en': 'Use Image search engine to search information for the given query',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='3c44f9ad-be5c-4e6c-a9d8-1426b23828a0',
            name='app.cosight.search_toolkit.search_google',
            description_zh='使用图片搜索工具搜索需要的图片信息',
            description_en='Get search results using Image search engine',
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["query"]
            }
        )
    }


def browser_use_skill():
    return {
        'skill_name': 'browser_use',
        'skill_type': "function",
        'display_name_zh': '浏览器交互模拟',
        'display_name_en': 'Browser Interaction Simulation',
        'description_zh': '模拟浏览器交互以解决需要多步操作的任务',
        'description_en': 'Simulate browser interaction to solve tasks requiring multi-step actions',
        'semantic_apis': ["api_browser_simulation"],
        'function': SkillFunction(
            id='2c44f9ad-be5c-4e6c-a9d8-1426b23828a1',
            name='app.cosight.browser_toolkit.browser_use',
            description_zh='通过模拟浏览器交互解决复杂任务',
            description_en='Solve complex tasks by simulating browser interactions',
            parameters={
                "type": "object",
                "properties": {
                    "task_prompt": {
                        "type": "string",
                        "description_zh": "需要解决的任务描述",
                        "description_en": "Task description to be solved"
                    }
                },
                "required": ["task_prompt"]
            }
        )
    }


def fetch_website_content_skill():
    return {
        'skill_name': 'fetch_website_content',
        'skill_type': "function",
        'display_name_zh': '网页内容爬取',
        'display_name_en': 'Fetch Website Content',
        'description_zh': '网页内容爬取',
        'description_en': 'Fetch Website Content',
        'semantic_apis': ["api_browser_simulation"],
        'function': SkillFunction(
            id='2c44f9ad-be5c-4e6c-a9d8-1426b23828a1',
            name='app.cosight.browser_toolkit.browser_use',
            description_zh='网页内容爬取',
            description_en='Fetch Website Content',
            parameters={
                "type": "object",
                "properties": {
                    "website_url": {
                        "type": "string",
                        "description_zh": "页面链接",
                        "description_en": "Website Url"
                    }
                },
                "required": ["website_url"]
            }
        )
    }


def mark_step_skill():
    return {
        'skill_name': 'mark_step',
        'skill_type': "function",
        'display_name_zh': '标记步骤',
        'display_name_en': 'Mark Step',
        'description_zh': '标记计划中的步骤状态，包括执行结果、遇到的问题、下一步建议等信息',
        'description_en': 'Mark the status of a step in the plan, including execution results, problems encountered, and suggestions for next steps',
        'semantic_apis': ["api_planning"],
        'function': SkillFunction(
            id='6d7f9a2b-c6e3-4f8d-b1a2-3e4f5d6c7b8c',
            name='app.cosight.tool.act_toolkit.ActToolkit.mark_step',
            description_zh='更新步骤的状态和备注，状态包括：已完成、受阻',
            description_en='Update the status and notes of a step, with status options: completed, blocked',
            parameters={
                "type": "object",
                "properties": {
                    'step_index': {
                        'type': 'integer',
                        'description_zh': '要更新的步骤索引（从0开始）',
                        'description_en': 'Index of the step to update (starting from 0)'
                    },
                    'step_status': {
                        'type': 'string',
                        'enum': ['completed', 'blocked'],
                        'description_zh': '步骤的新状态：\n'
                                          '- "completed": 步骤已完全执行且正确解决问题\n'
                                          '- "blocked": 步骤无法完成或未正确解决问题',
                        'description_en': 'New status for the step:\n'
                                          '- "completed": Step is fully executed AND correctly solved the problem\n'
                                          '- "blocked": Step cannot be completed OR did not correctly solve the problem'
                    },
                    'step_notes': {
                        'type': 'string',
                        'description_zh': '步骤的备注信息，包括：\n'
                                          '- 详细执行结果\n'
                                          '- 遇到的问题\n'
                                          '- 下一步建议\n'
                                          '- 对其他步骤的依赖\n'
                                          '- 生成的任何文件的绝对路径',
                        'description_en': 'Additional notes for the step, including:\n'
                                          '- Detailed execution results\n'
                                          '- Problems encountered\n'
                                          '- Suggestions for next steps\n'
                                          '- Dependencies on other steps\n'
                                          '- Absolute file paths of any generated files'
                    }
                },
                'required': ['step_index', 'step_status', 'step_notes']
            }
        )
    }


def file_saver_skill():
    return {
        'skill_name': 'file_saver',
        'skill_type': "function",
        'display_name_zh': '文件保存（内容必填）',
        'display_name_en': 'File Saver (content required)',
        'description_zh': '将内容保存到指定路径的本地文件中，必须提供content参数作为文件内容。支持文本和二进制文件（如图片、音频、视频）。默认模式为追加，以保留文件原有内容',
        'description_en': 'Save content to a local file at a specified path. IMPORTANT: You MUST provide the content parameter with the text to save. Supports both text and binary files (e.g., images, audio, video). Default mode is append to preserve existing file content',
        'semantic_apis': ["api_file_management"],
        'function': SkillFunction(
            id='5c44f9ad-be5c-4e6c-a9d8-1426b23828a2',
            name='app.cosight.tool.file_toolkit.FileToolkit.file_saver',
            description_zh='将内容保存到指定路径的文件中，必须提供content参数指定要保存的内容。支持文本和二进制文件。默认模式为追加',
            description_en='Save content to a file at the specified path. IMPORTANT: You MUST provide the content parameter with the text to save. Supports both text and binary files. Default mode is append',
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description_zh": "【必须提供】要保存的内容（文本或base64编码的二进制数据）",
                        "description_en": "REQUIRED: Content to be saved (text or base64 encoded binary data). This is the actual text that will be written to the file."
                    },
                    "file_path": {
                        "type": "string",
                        "description_zh": "要保存文件的绝对路径（需在工作区内，WORKSPACE_PATH环境变量指定）",
                        "description_en": "Absolute path of the file to save (must be within workspace specified by WORKSPACE_PATH environment variable)"
                    },
                    "mode": {
                        "type": "string",
                        "description_zh": "文件打开模式：'a' 追加（默认），'w' 写入",
                        "description_en": "File opening mode: 'a' for append (default), 'w' for write",
                        "enum": ["a", "w"],
                        "default": "a"
                    },
                    "binary": {
                        "type": "boolean",
                        "description_zh": "是否为二进制文件模式",
                        "description_en": "Whether to use binary mode",
                        "default": False
                    }
                },
                "required": ["content", "file_path"]
            }
        )
    }


def file_read_skill():
    return {
        'skill_name': 'file_read',
        'skill_type': "function",
        'display_name_zh': '文件读取',
        'display_name_en': 'File Read',
        'description_zh': '读取指定路径的本地文件内容，支持文本和二进制文件（如图片、音频、视频）',
        'description_en': 'Read content from a local file at a specified path. Supports both text and binary files (e.g., images, audio, video)',
        'semantic_apis': ["api_file_management"],
        'function': SkillFunction(
            id='6c44f9ad-be5c-4e6c-a9d8-1426b23828a3',
            name='app.cosight.tool.file_toolkit.FileToolkit.file_read',
            description_zh='读取指定路径的文件内容，支持文本和二进制文件',
            description_en='Read content from a file at the specified path. Supports both text and binary files',
            parameters={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description_zh": "要读取的文件的绝对路径（需在工作区内，WORKSPACE_PATH环境变量指定）",
                        "description_en": "Absolute path of the file to read (must be within workspace specified by WORKSPACE_PATH environment variable)"
                    },
                    "start_line": {
                        "type": "integer",
                        "description_zh": "起始行号（从0开始，仅文本文件）",
                        "description_en": "Starting line number (0-based, text files only)",
                        "minimum": 0
                    },
                    "end_line": {
                        "type": "integer",
                        "description_zh": "结束行号（不包括该行，仅文本文件）",
                        "description_en": "Ending line number (exclusive, text files only)",
                        "minimum": 0
                    },
                    "sudo": {
                        "type": "boolean",
                        "description_zh": "是否使用sudo权限",
                        "description_en": "Whether to use sudo privileges",
                        "default": False
                    },
                    "binary": {
                        "type": "boolean",
                        "description_zh": "是否为二进制文件模式",
                        "description_en": "Whether to use binary mode",
                        "default": False
                    }
                },
                "required": ["file"]
            }
        )
    }


def file_str_replace_skill():
    return {
        'skill_name': 'file_str_replace',
        'skill_type': "function",
        'display_name_zh': '文件字符串替换',
        'display_name_en': 'File String Replacement',
        'description_zh': '替换文件中的指定字符串，用于更新文件内容或修复代码错误',
        'description_en': 'Replace specified string in a file. Use for updating specific content in files or fixing errors in code',
        'semantic_apis': ["api_file_management"],
        'function': SkillFunction(
            id='7c44f9ad-be5c-4e6c-a9d8-1426b23828a4',
            name='app.cosight.tool.file_toolkit.FileToolkit.file_str_replace',
            description_zh='替换文件中的指定字符串',
            description_en='Replace specified string in a file',
            parameters={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description_zh": "要执行替换操作的文件路径",
                        "description_en": "Absolute path of the file to perform replacement on"
                    },
                    "old_str": {
                        "type": "string",
                        "description_zh": "要被替换的原始字符串",
                        "description_en": "Original string to be replaced"
                    },
                    "new_str": {
                        "type": "string",
                        "description_zh": "用于替换的新字符串",
                        "description_en": "New string to replace wiEth"
                    },
                    "sudo": {
                        "type": "boolean",
                        "description_zh": "是否使用sudo权限",
                        "description_en": "Whether to use sudo privileges",
                        "default": False
                    }
                },
                "required": ["file", "old_str", "new_str"]
            }
        )
    }


def file_find_in_content_skill():
    return {
        'skill_name': 'file_find_in_content',
        'skill_type': "function",
        'display_name_zh': '文件内容查找',
        'display_name_en': 'Find in File Content',
        'description_zh': '在文件内容中搜索匹配的文本，用于查找特定内容或模式',
        'description_en': 'Search for matching text within file content. Use for finding specific content or patterns in files',
        'semantic_apis': ["api_file_management"],
        'function': SkillFunction(
            id='8c44f9ad-be5c-4e6c-a9d8-1426b23828a5',
            name='app.cosight.tool.file_toolkit.FileToolkit.file_find_in_content',
            description_zh='在文件内容中搜索匹配的文本',
            description_en='Search for matching text within file content',
            parameters={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description_zh": "要搜索的文件路径",
                        "description_en": "Absolute path of the file to search within"
                    },
                    "regex": {
                        "type": "string",
                        "description_zh": "要匹配的正则表达式模式",
                        "description_en": "Regular expression pattern to match"
                    },
                    "sudo": {
                        "type": "boolean",
                        "description_zh": "是否使用sudo权限",
                        "description_en": "Whether to use sudo privileges",
                        "default": False
                    }
                },
                "required": ["file", "regex"]
            }
        )
    }


def register_mcp_tools():
    # 解析mcp工具
    skills = JsonUtil.read_all_data(mcp_server_config_dir)
    return skills


def deep_search_skill():
    return {
        'skill_name': 'deep_search',
        'skill_type': "function",
        'display_name_zh': '深度搜索',
        'display_name_en': 'Deep Search',
        'description_zh': '使用深度搜索引擎进行信息检索和分析',
        'description_en': 'Use deep-search engine for multi-source information retrieval and analysis',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='8d5e7f3b-a4c2-4d1b-9f6e-2c8b9d7e1234',
            name='app.cosight.tool.deep_search_toolkit.deep_search',
            description_zh='通过深度搜索引擎获取搜索结果并进行分析总结',
            description_en='Get and analyze search results using deep-search engine with multiple sources',
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["query"]
            }
        )
    }


def search_baidu_skill():
    return {
        'skill_name': 'search_baidu',
        'skill_type': "function",
        'display_name_zh': '百度内容搜索',
        'display_name_en': 'Baidu Search',
        'description_zh': '使用百度搜索引擎进行信息检索和分析',
        'description_en': 'Use Baidu search engine for multi-source information retrieval and analysis',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='8d5e7f3b-a4c2-4d1b-9f6e-2c8b9d7e1234',
            name='app.cosight.tool.deep_search_toolkit.deep_search',
            description_zh='通过百度内容搜索引擎获取搜索结果并进行分析总结',
            description_en='Get and analyze search results using Baidusearch engine with multiple sources',
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description_zh": "要搜索的查询内容",
                        "description_en": "Query to be searched"
                    }
                },
                "required": ["query"]
            }
        )
    }


def ask_question_about_video_skill():
    return {
        'skill_name': 'ask_question_about_video',
        'skill_type': "function",
        'display_name_zh': '获取视频内容',
        'display_name_en': 'Video Content analyse',
        'description_zh': '获取视频内容',
        'description_en': 'Ask a question about the video.',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='8d5e7f3b-a4c2-4d1b-9f6e-2c8b9d7e1234',
            name='app.cosight.tool.deep_search_toolkit.deep_search',
            description_zh='获取视频内容',
            description_en='Ask a question about the video.',
            parameters={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description_zh": "视频路径",
                        "description_en": "Video path"
                    },
                    "question": {
                        "type": "string",
                        "description_zh": "要提问的问题",
                        "description_en": "question"
                    }
                },

                "required": ["video_path", "question"]
            }
        )
    }


def audio_recognition_skill():
    return {
        'skill_name': 'audio_recognition',
        'skill_type': "function",
        'display_name_zh': '根据任务描述和输入音频识别输出音频内容',
        'display_name_en': 'Identify the output audio content based on the task description and input audio',
        'description_zh': '根据任务描述和输入音频识别输出音频内容',
        'description_en': 'Identify the output audio content based on the task description and input audio',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='8d5e7f3b-a4c2-4d1b-9f6e-2c8b9d7e1234',
            name='app.cosight.tool.deep_search_toolkit.deep_search',
            description_zh='根据任务描述和输入音频识别输出音频内容',
            description_en='Identify the output audio content based on the task description and input audio',
            parameters={
                "type": "object",
                "properties": {
                    "audio_path": {
                        "type": "string",
                        "description_zh": "音频路径",
                        "description_en": "Audio path"
                    },
                    "task_prompt": {
                        "type": "string",
                        "description_zh": "任务内容描述",
                        "description_en": "task description"
                    }
                },

                "required": ["audio_path", "task_prompt"]
            }
        )
    }


def ask_question_about_image_skill():
    return {
        'skill_name': 'ask_question_about_image',
        'skill_type': "function",
        'display_name_zh': '根据任务描述解析图片内容',
        'display_name_en': 'Image Content analyse',
        'description_zh': '根据任务描述解析图片内容',
        'description_en': 'Ask a question about the image.',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='8d5e7f3b-a4c2-4d1b-9f6e-2c8b9d7e1234',
            name='app.cosight.tool.deep_search_toolkit.deep_search',
            description_zh='图片内容解析',
            description_en='Ask a question about the image.',
            parameters={
                "type": "object",
                "properties": {
                    "image_path_url": {
                        "type": "string",
                        "description_zh": "图片路径",
                        "description_en": "Image path"
                    },
                    "task_prompt": {
                        "type": "string",
                        "description_zh": "任务内容描述",
                        "description_en": "task description"
                    }
                },

                "required": ["image_path_url", "task_prompt"]
            }
        )
    }


def extract_document_content_skill():
    return {
        'skill_name': 'extract_document_content',
        'skill_type': "function",
        'display_name_zh': '读取jsonl，json，jsonld，zip，md，py，xml，docx，pdf等类型文件内容',
        'display_name_en': 'Read contents from files of types such as .jsonl, .json, .jsonld, .zip, .md, .py, .xml, .docx, .pdf, and others.',
        'description_zh': '读取jsonl，json，jsonld，zip，md，py，xml，docx，pdf等类型文件内容',
        'description_en': 'Read contents from files of types such as .jsonl, .json, .jsonld, .zip, .md, .py, .xml, .docx, .pdf, and others.',
        'semantic_apis': ["api_search"],
        'function': SkillFunction(
            id='8d5e7f3b-a4c2-4d1b-9f6e-2c8b9d7e1234',
            name='app.cosight.tool.deep_search_toolkit.deep_search',
            description_zh='读取jsonl，json，jsonld，zip，md，py，xml，docx，pdf等类型文件内容',
            description_en='Read contents from files of types such as .jsonl, .json, .jsonld, .zip, .md, .py, .xml, .docx, .pdf, and others.',
            parameters={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string",
                        "description_zh": "文件路径",
                        "description_en": "File path"
                    }
                },

                "required": ["document_path"]
            }
        )
    }

def create_html_report_skill():
    """为Agent框架提供的HTML报告生成技能定义
    大模型只需选择此函数，不需要传入参数
    函数执行过程中会通过LLM获取必要的参数
    """
    return {
        'skill_name': 'create_html_report',
        'skill_type': "function",
        'display_name_zh': 'HTML报告生成（只在生成最终报告时调用此函数，过程中的报告保存不要调用这个函数）',
        'display_name_en': 'Generate HTML Report (This function is only called when generating the final report. Do not call this function when saving the report in the process.)',
        'description_zh': '根据工作区文本文件生成结构化的商务风格HTML报告，包含自动生成的图表和导航栏。此功能可以自动分析工作区中的文本文件并创建可视化报告。（只在生成最终报告时调用此函数，过程中的报告保存不要调用这个函数）',
        'description_en': 'Generate structured business-style HTML reports from workspace text files, with auto-generated charts and navigation. This function automatically analyzes text files in the workspace and creates a visualization report.This function is only called when generating the final report. Do not call this function when saving the report in the process.',
        'semantic_apis': ["api_report_generation", "api_visualization"],
        'function': SkillFunction(
            id='8e57b2a0-c6e8-4d3b-9f1d-b02a4c6f8235',
            name='app.cosight.tool.html_visualization_toolkit.main',
            description_zh='基于工作区中的文本文件，自动生成包含可视化图表的商务风格HTML报告。（只在生成最终报告时调用此函数，过程中的报告保存不要调用这个函数）',
            description_en='Automatically generate business-style HTML reports with visualizations based on text files in the workspace. This function is only called when generating the final report. Do not call this function when saving the report in the process.',
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    }


def fetch_website_content_with_images_skill():
    return {
        'skill_name': 'fetch_website_content_with_images',
        'skill_type': "function",
        'display_name_zh': '网页内容爬取（含图片）',
        'display_name_en': 'Fetch Website Content with Images',
        'description_zh': '获取网页内容并提取所有图片信息，包括img标签和CSS背景图片',
        'description_en': 'Fetch website content and extract all image information including img tags and CSS background images',
        'semantic_apis': ["api_browser_simulation"],
        'function': SkillFunction(
            id='3c44f9ad-be5c-4e6c-a9d8-1426b23828a2',
            name='app.cosight.tool.scrape_website_toolkit.fetch_website_content_with_images',
            description_zh='获取网页内容并提取图片信息，返回文本内容和图片详细信息',
            description_en='Fetch website content and extract image information, return text content and detailed image info',
            parameters={
                "type": "object",
                "properties": {
                    "website_url": {
                        "type": "string",
                        "description_zh": "要抓取的网页URL",
                        "description_en": "Website URL to scrape"
                    }
                },
                "required": ["website_url"]
            }
        )
    }


def fetch_website_images_only_skill():
    return {
        'skill_name': 'fetch_website_images_only',
        'skill_type': "function",
        'display_name_zh': '网页图片提取',
        'display_name_en': 'Fetch Website Images Only',
        'description_zh': '仅提取网页中的图片信息，不返回文本内容',
        'description_en': 'Extract only image information from website without text content',
        'semantic_apis': ["api_browser_simulation"],
        'function': SkillFunction(
            id='4c44f9ad-be5c-4e6c-a9d8-1426b23828a3',
            name='app.cosight.tool.scrape_website_toolkit.fetch_website_images_only',
            description_zh='仅提取网页图片信息，包括img标签和CSS背景图片',
            description_en='Extract only website image information including img tags and CSS background images',
            parameters={
                "type": "object",
                "properties": {
                    "website_url": {
                        "type": "string",
                        "description_zh": "要抓取的网页URL",
                        "description_en": "Website URL to scrape"
                    }
                },
                "required": ["website_url"]
            }
        )
    }

