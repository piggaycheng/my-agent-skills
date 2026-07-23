# /// script
# dependencies = [
#     "google-api-python-client",
#     "google-auth",
#     "google-auth-httplib2",
#     "google-auth-oauthlib",
# ]
# ///

import os
import sys
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def rgb_to_dict(r, g, b):
    return {"red": r / 255.0, "green": g / 255.0, "blue": b / 255.0}

def find_default_user_email():
    env_email = os.getenv("USER_GOOGLE_EMAIL") or os.getenv("GOOGLE_USER_EMAIL")
    if env_email:
        return env_email
        
    workspace_dir = os.getenv("WORKSPACE_MCP_CREDENTIALS_DIR") or os.getenv("GOOGLE_MCP_CREDENTIALS_DIR")
    dirs_to_check = []
    if workspace_dir:
        dirs_to_check.append(os.path.expanduser(workspace_dir))
    dirs_to_check.append(os.path.expanduser("~/.google_workspace_mcp/credentials"))
    dirs_to_check.append(os.path.join(os.getcwd(), ".credentials"))

    for d in dirs_to_check:
        if os.path.exists(d):
            try:
                for f in os.listdir(d):
                    if f.endswith(".json") and f != "oauth_states.json":
                        return f[:-5]
            except Exception:
                pass
    return "user@example.com"

def get_credentials(user_email):
    workspace_dir = os.getenv("WORKSPACE_MCP_CREDENTIALS_DIR")
    google_dir = os.getenv("GOOGLE_MCP_CREDENTIALS_DIR")
    
    dirs_to_check = []
    if workspace_dir:
        dirs_to_check.append(os.path.expanduser(workspace_dir))
    if google_dir:
        dirs_to_check.append(os.path.expanduser(google_dir))
    dirs_to_check.append(os.path.expanduser("~/.google_workspace_mcp/credentials"))
    dirs_to_check.append(os.path.join(os.getcwd(), ".credentials"))

    for d in dirs_to_check:
        creds_path = os.path.join(d, f"{user_email}.json")
        if os.path.exists(creds_path):
            try:
                return Credentials.from_authorized_user_file(creds_path)
            except Exception as e:
                print(f"Warning: Failed to load credentials from {creds_path}: {e}")
                
    print(f"Error: Credentials file for '{user_email}' not found in any of {dirs_to_check}")
    sys.exit(1)

def find_template_id(drive_service, template_name="盟立集團-新版ppt-2"):
    query = f"name contains '{template_name}' and mimeType = 'application/vnd.google-apps.presentation' and trashed = false"
    res = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
        
    query_fallback = f"name contains '{template_name}' and trashed = false"
    res_fallback = drive_service.files().list(q=query_fallback, fields="files(id, name)").execute()
    files_fallback = res_fallback.get("files", [])
    if files_fallback:
        return files_fallback[0]["id"]
        
    return None

def find_title_placeholder_id(slides_service, pres_id, page_id):
    try:
        page = slides_service.presentations().pages().get(presentationId=pres_id, pageObjectId=page_id).execute()
        for el in page.get("pageElements", []):
            if el.get("shape", {}).get("placeholder", {}).get("type") == "TITLE":
                return el.get("objectId")
    except Exception as e:
        print(f"Warning: Failed to get title placeholder for page {page_id}: {e}")
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run generate_weekly_report_gslides.py <json_path> [user_email] [user_name]")
        sys.exit(1)
        
    json_path = sys.argv[1]
    user_email = sys.argv[2] if len(sys.argv) > 2 else find_default_user_email()
    override_user_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found: {json_path}")
        sys.exit(1)
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    issues = data.get("issues", [])
    
    creds = get_credentials(user_email)
    drive_service = build('drive', 'v3', credentials=creds)
    slides_service = build('slides', 'v1', credentials=creds)

    # Prioritize Google account displayName as top priority
    google_display_name = None
    try:
        about = drive_service.about().get(fields="user").execute()
        google_display_name = about.get("user", {}).get("displayName")
    except Exception as e:
        print(f"Warning: Could not fetch Google user displayName: {e}")

    user_name = google_display_name or override_user_name or data.get("user_name") or data.get("reporter") or "王小明"
    
    # Calculate Friday date (YYYYMMDD)
    if start_date:
        try:
            monday_dt = datetime.strptime(start_date, "%Y-%m-%d")
            friday_dt = monday_dt + timedelta(days=4)
            friday_str = friday_dt.strftime("%Y%m%d")
        except Exception:
            friday_str = datetime.now().strftime("%Y%m%d")
    else:
        friday_str = datetime.now().strftime("%Y%m%d")
        
    file_name = f"{user_name}_週報_{friday_str}"
    
    # Find template "盟立集團-新版ppt-2"
    template_id = find_template_id(drive_service, "盟立集團-新版ppt-2")
    if not template_id:
        print("Error: Template '盟立集團-新版ppt-2' not found on Google Drive.")
        sys.exit(1)
        
    print(f"Copying template '盟立集團-新版ppt-2' (ID: {template_id}) to '{file_name}'...")
    copied_file = drive_service.files().copy(fileId=template_id, body={'name': file_name}).execute()
    pres_id = copied_file.get('id')
    
    # Get presentation details
    pres = slides_service.presentations().get(presentationId=pres_id).execute()
    slides_list = pres.get('slides', [])
    
    if len(slides_list) < 3:
        print("Error: Template must have at least 3 slides to extract custom layout templates.")
        sys.exit(1)
        
    # Slide 3 defines custom layout (e.g. p9 / '3_自訂版面配置')
    content_layout_id = slides_list[2].get('slideProperties', {}).get('layoutObjectId')
    
    requests = []
    
    # Mirle Official Theme Color Palette
    color_header_bg = rgb_to_dict(68, 114, 196)   # #4472C4 Mirle Theme Blue ACCENT1
    color_white = rgb_to_dict(255, 255, 255)      # #FFFFFF White
    color_card_bg = rgb_to_dict(247, 250, 252)    # #F7FAFC Soft Gray-Blue
    color_dark_text = rgb_to_dict(44, 62, 80)     # #2C3E50 Dark Slate Text
    color_alt_row = rgb_to_dict(242, 244, 248)    # #F2F4F8 Light Blue-Gray Alternating Row
    color_border = rgb_to_dict(208, 215, 226)     # #D0D7E2 Soft Border
    color_navy = rgb_to_dict(26, 54, 93)          # #1A365D Title Navy
    
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    subtitle_content = f"報告期間：{start_date} ~ {end_date}\n產出時間：{current_date_str}\n報告人員：{user_name}"
    
    # 1. Update Slide 1 Title & Subtitle in template placeholders
    slide_1_id = slides_list[0].get('objectId')
    requests.append({
        'replaceAllText': {
            'replaceText': file_name,
            'containsText': {'text': '按一下以編輯母片標題樣式'},
            'pageObjectIds': [slide_1_id]
        }
    })
    requests.append({
        'replaceAllText': {
            'replaceText': subtitle_content,
            'containsText': {'text': '按一下以編輯母片副標題樣式'},
            'pageObjectIds': [slide_1_id]
        }
    })
    
    # Delete slide 2 and subsequent initial slides from template copy
    for s in slides_list[1:]:
        requests.append({'deleteObject': {'objectId': s.get('objectId')}})
        
    # Execute phase 1: update title slide and delete template placeholder slides
    slides_service.presentations().batchUpdate(presentationId=pres_id, body={'requests': requests}).execute()
    
    # Phase 2: Build Table and Detail Slides using the template content layout!
    chunk_size = 10
    issue_chunks = [issues[i:i + chunk_size] for i in range(0, len(issues), chunk_size)]
    
    slide_configs = []
    phase2_requests = []
    
    for chunk_idx, chunk in enumerate(issue_chunks):
        table_slide_id = f"slide_table_{chunk_idx + 1}"
        phase2_requests.append({
            'createSlide': {
                'objectId': table_slide_id,
                'slideLayoutReference': {
                    'layoutId': content_layout_id
                }
            }
        })
        
        title_text = "本週 Issue 狀態彙整"
        if len(issue_chunks) > 1:
            title_text += f" ({chunk_idx + 1}/{len(issue_chunks)})"
            
        slide_configs.append({
            'type': 'table',
            'slide_id': table_slide_id,
            'title': title_text,
            'chunk': chunk
        })
        
    for idx, issue in enumerate(issues):
        detail_slide_id = f"slide_detail_{idx + 1}"
        phase2_requests.append({
            'createSlide': {
                'objectId': detail_slide_id,
                'slideLayoutReference': {
                    'layoutId': content_layout_id
                }
            }
        })
        
        issue_id = issue.get("id", "")
        tracker = issue.get("tracker", "Issue")
        subject = issue.get("subject", "")
        detail_slide_title = f"[{tracker}] #{issue_id}: {subject}"
        if len(detail_slide_title) > 42:
            detail_slide_title = detail_slide_title[:40] + "..."
            
        slide_configs.append({
            'type': 'detail',
            'slide_id': detail_slide_id,
            'title': detail_slide_title,
            'issue': issue,
            'index': idx + 1
        })
        
    # Execute slide creations
    slides_service.presentations().batchUpdate(presentationId=pres_id, body={'requests': phase2_requests}).execute()
    
    # Phase 3: Populate Title placeholders and content elements on created slides
    phase3_requests = []
    
    for cfg in slide_configs:
        slide_id = cfg['slide_id']
        title_text = cfg['title']
        
        title_shape_id = find_title_placeholder_id(slides_service, pres_id, slide_id)
        if title_shape_id:
            phase3_requests.append({
                'insertText': {
                    'objectId': title_shape_id,
                    'text': title_text,
                    'insertionIndex': 0
                }
            })
            phase3_requests.append({
                'updateTextStyle': {
                    'objectId': title_shape_id,
                    'textRange': {'type': 'ALL'},
                    'style': {
                        'fontFamily': 'Microsoft JhengHei',
                        'bold': True
                    },
                    'fields': 'fontFamily,bold'
                }
            })
        else:
            t_header_id = f"title_fallback_{slide_id}"
            phase3_requests.append({
                'createShape': {
                    'objectId': t_header_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {'width': {'magnitude': 860, 'unit': 'PT'}, 'height': {'magnitude': 45, 'unit': 'PT'}},
                        'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 50, 'translateY': 40, 'unit': 'PT'}
                    }
                }
            })
            phase3_requests.append({
                'insertText': {'objectId': t_header_id, 'text': title_text, 'insertionIndex': 0}
            })
            phase3_requests.append({
                'updateTextStyle': {
                    'objectId': t_header_id,
                    'textRange': {'type': 'ALL'},
                    'style': {
                        'fontFamily': 'Microsoft JhengHei',
                        'fontSize': {'magnitude': 22, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {'opaqueColor': {'rgbColor': color_white}}
                    },
                    'fields': 'fontFamily,fontSize,bold,foregroundColor'
                }
            })
            
        if cfg['type'] == 'table':
            chunk = cfg['chunk']
            table_id = f"table_obj_{slide_id}"
            rows_count = len(chunk) + 1
            cols_count = 6
            phase3_requests.append({
                'createTable': {
                    'objectId': table_id,
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {'width': {'magnitude': 860, 'unit': 'PT'}, 'height': {'magnitude': rows_count * 28 + 35, 'unit': 'PT'}},
                        'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 50, 'translateY': 120, 'unit': 'PT'}
                    },
                    'rows': rows_count,
                    'columns': cols_count
                }
            })
            
            # Apply Table Border Styling (Mirle Soft Border)
            phase3_requests.append({
                'updateTableBorderProperties': {
                    'objectId': table_id,
                    'tableBorderProperties': {
                        'tableBorderFill': {
                            'solidFill': {'color': {'rgbColor': color_border}}
                        },
                        'weight': {'magnitude': 1, 'unit': 'PT'},
                        'dashStyle': 'SOLID'
                    },
                    'fields': 'tableBorderFill.solidFill.color,weight,dashStyle'
                }
            })
            
            headers = ["ID", "類型", "主旨", "狀態", "負責人", "專案名稱"]
            for col_idx, text in enumerate(headers):
                phase3_requests.append({
                    'insertText': {
                        'objectId': table_id,
                        'cellLocation': {'rowIndex': 0, 'columnIndex': col_idx},
                        'text': text,
                        'insertionIndex': 0
                    }
                })
                # Header Cell Fill: Mirle Theme Blue ACCENT1 (#4472C4)
                phase3_requests.append({
                    'updateTableCellProperties': {
                        'objectId': table_id,
                        'tableRange': {'location': {'rowIndex': 0, 'columnIndex': col_idx}, 'rowSpan': 1, 'columnSpan': 1},
                        'tableCellProperties': {
                            'tableCellBackgroundFill': {'solidFill': {'color': {'rgbColor': color_header_bg}}}
                        },
                        'fields': 'tableCellBackgroundFill.solidFill.color'
                    }
                })
                
            for row_idx, issue in enumerate(chunk, 1):
                row_data = [
                    str(issue.get("id", "")),
                    issue.get("tracker", ""),
                    issue.get("subject", ""),
                    issue.get("status", ""),
                    issue.get("assignee", "") or "未指派",
                    issue.get("project", "")
                ]
                row_bg = color_alt_row if row_idx % 2 == 1 else color_white
                for col_idx, val in enumerate(row_data):
                    phase3_requests.append({
                        'insertText': {
                            'objectId': table_id,
                            'cellLocation': {'rowIndex': row_idx, 'columnIndex': col_idx},
                            'text': str(val),
                            'insertionIndex': 0
                        }
                    })
                    phase3_requests.append({
                        'updateTableCellProperties': {
                            'objectId': table_id,
                            'tableRange': {'location': {'rowIndex': row_idx, 'columnIndex': col_idx}, 'rowSpan': 1, 'columnSpan': 1},
                            'tableCellProperties': {
                                'tableCellBackgroundFill': {'solidFill': {'color': {'rgbColor': row_bg}}}
                            },
                            'fields': 'tableCellBackgroundFill.solidFill.color'
                        }
                    })
                    
        elif cfg['type'] == 'detail':
            issue = cfg['issue']
            idx = cfg['index']
            
            # Left Column Card (Round Rectangle)
            left_card_id = f"left_card_{idx}"
            phase3_requests.append({
                'createShape': {
                    'objectId': left_card_id,
                    'shapeType': 'ROUND_RECTANGLE',
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {'width': {'magnitude': 250, 'unit': 'PT'}, 'height': {'magnitude': 370, 'unit': 'PT'}},
                        'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 50, 'translateY': 120, 'unit': 'PT'}
                    }
                }
            })
            phase3_requests.append({
                'updateShapeProperties': {
                    'objectId': left_card_id,
                    'shapeProperties': {
                        'shapeBackgroundFill': {'solidFill': {'color': {'rgbColor': color_card_bg}}},
                        'outline': {'propertyState': 'NOT_RENDERED'}
                    },
                    'fields': 'shapeBackgroundFill.solidFill.color,outline.propertyState'
                }
            })
            
            meta_text = (
                f"專案名稱\n{issue.get('project', '')}\n\n"
                f"目前狀態\n{issue.get('status', '')}\n\n"
                f"負責人員\n{issue.get('assignee', '') or '未指派'}\n\n"
                f"建立日期\n{issue.get('created_on', '')[:10]}"
            )
            phase3_requests.append({
                'insertText': {'objectId': left_card_id, 'text': meta_text, 'insertionIndex': 0}
            })
            phase3_requests.append({
                'updateTextStyle': {
                    'objectId': left_card_id,
                    'textRange': {'type': 'ALL'},
                    'style': {
                        'fontFamily': 'Microsoft JhengHei',
                        'fontSize': {'magnitude': 12, 'unit': 'PT'},
                        'foregroundColor': {'opaqueColor': {'rgbColor': color_dark_text}}
                    },
                    'fields': 'fontFamily,fontSize,foregroundColor'
                }
            })
            
            # Right Column Content Box
            right_box_id = f"right_box_{idx}"
            phase3_requests.append({
                'createShape': {
                    'objectId': right_box_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {'width': {'magnitude': 590, 'unit': 'PT'}, 'height': {'magnitude': 370, 'unit': 'PT'}},
                        'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 320, 'translateY': 120, 'unit': 'PT'}
                    }
                }
            })
            
            key_points = issue.get("key_points", [])
            if not key_points:
                right_text = "工作進度與實作細節：\n\n• 目前尚無詳細日誌進度記錄。"
            else:
                right_text = "工作進度與實作細節：\n\n" + "\n".join(f"• {pt}" for pt in key_points)
                
            phase3_requests.append({
                'insertText': {'objectId': right_box_id, 'text': right_text, 'insertionIndex': 0}
            })
            phase3_requests.append({
                'updateTextStyle': {
                    'objectId': right_box_id,
                    'textRange': {'type': 'ALL'},
                    'style': {
                        'fontFamily': 'Microsoft JhengHei',
                        'fontSize': {'magnitude': 12, 'unit': 'PT'},
                        'foregroundColor': {'opaqueColor': {'rgbColor': color_dark_text}}
                    },
                    'fields': 'fontFamily,fontSize,foregroundColor'
                }
            })
            
    # Execute batchUpdate in safe chunks of 80
    batch_size = 80
    for i in range(0, len(phase3_requests), batch_size):
        chunk_reqs = phase3_requests[i:i + batch_size]
        slides_service.presentations().batchUpdate(
            presentationId=pres_id,
            body={'requests': chunk_reqs}
        ).execute()
        
    url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    print(f"SUCCESS: Google Slides weekly report generated successfully using official template layout and colors!")
    print(f"Presentation Title: {file_name}")
    print(f"Presentation ID: {pres_id}")
    print(f"Google Slides URL: {url}")

if __name__ == "__main__":
    main()
