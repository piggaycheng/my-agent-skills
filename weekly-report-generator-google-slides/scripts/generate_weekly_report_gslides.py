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

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run generate_weekly_report_gslides.py <json_path> [user_email] [user_name]")
        sys.exit(1)
        
    json_path = sys.argv[1]
    user_email = sys.argv[2] if len(sys.argv) > 2 else "piggaycheng123@gmail.com"
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
        
    # File name format: <使用者名稱>_週報_<這周週五的年月日>
    file_name = f"{user_name}_週報_{friday_str}"
    
    # Find template "盟立集團-新版ppt-2"
    template_id = find_template_id(drive_service, "盟立集團-新版ppt-2")
    
    if template_id:
        print(f"Found template '盟立集團-新版ppt-2' (ID: {template_id}). Copying template...")
        copied_file = drive_service.files().copy(fileId=template_id, body={'name': file_name}).execute()
        pres_id = copied_file.get('id')
    else:
        print("Warning: Template '盟立集團-新版ppt-2' not found on Google Drive. Creating new presentation...")
        pres = slides_service.presentations().create(body={'title': file_name}).execute()
        pres_id = pres.get('presentationId')
        
    # Get presentation details
    pres = slides_service.presentations().get(presentationId=pres_id).execute()
    slides_list = pres.get('slides', [])
    
    requests = []
    
    # Color palette
    color_navy = rgb_to_dict(26, 54, 93)          # #1A365D Dark Navy
    color_white = rgb_to_dict(255, 255, 255)      # #FFFFFF White
    color_light_blue = rgb_to_dict(203, 213, 224) # #CBD5E0 Light Blue-Gray
    color_card_bg = rgb_to_dict(247, 250, 252)    # #F7FAFC Soft Gray-Blue
    color_dark_text = rgb_to_dict(45, 55, 72)      # #2D3748 Dark Charcoal
    color_alt_row = rgb_to_dict(241, 245, 249)     # #F1F5F9 Slate Light
    
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    subtitle_content = f"報告期間：{start_date} ~ {end_date}\n產出時間：{current_date_str}\n報告人員：{user_name}"
    
    # 1. Slide 1: Update Title Slide to match file_name
    if slides_list:
        slide_1_id = slides_list[0].get('objectId')
        # Replace placeholders in template Slide 1 if present
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
        
        # Add text box for title to ensure title matches file_name
        title_text_id = "title_text_1"
        subtitle_text_id = "subtitle_text_1"
        requests.append({
            'createShape': {
                'objectId': title_text_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': slide_1_id,
                    'size': {'width': {'magnitude': 620, 'unit': 'PT'}, 'height': {'magnitude': 80, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 50, 'translateY': 80, 'unit': 'PT'}
                }
            }
        })
        requests.append({
            'insertText': {'objectId': title_text_id, 'text': file_name, 'insertionIndex': 0}
        })
        requests.append({
            'updateTextStyle': {
                'objectId': title_text_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Microsoft JhengHei',
                    'fontSize': {'magnitude': 32, 'unit': 'PT'},
                    'bold': True,
                    'foregroundColor': {'opaqueColor': {'rgbColor': color_navy}}
                },
                'fields': 'fontFamily,fontSize,bold,foregroundColor'
            }
        })
        requests.append({
            'createShape': {
                'objectId': subtitle_text_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': slide_1_id,
                    'size': {'width': {'magnitude': 620, 'unit': 'PT'}, 'height': {'magnitude': 100, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 50, 'translateY': 180, 'unit': 'PT'}
                }
            }
        })
        requests.append({
            'insertText': {'objectId': subtitle_text_id, 'text': subtitle_content, 'insertionIndex': 0}
        })
        requests.append({
            'updateTextStyle': {
                'objectId': subtitle_text_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Microsoft JhengHei',
                    'fontSize': {'magnitude': 14, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'rgbColor': color_dark_text}}
                },
                'fields': 'fontFamily,fontSize,foregroundColor'
            }
        })
        
    # Delete slide 2 and subsequent initial slides from template
    if len(slides_list) > 1:
        for s in slides_list[1:]:
            requests.append({'deleteObject': {'objectId': s.get('objectId')}})
            
    # 2. Slide 2+: Issues Summary Table Slide(s)
    chunk_size = 10
    issue_chunks = [issues[i:i + chunk_size] for i in range(0, len(issues), chunk_size)]
    
    for chunk_idx, chunk in enumerate(issue_chunks):
        table_slide_id = f"slide_table_{chunk_idx + 1}"
        requests.append({
            'createSlide': {
                'objectId': table_slide_id
            }
        })
        
        title_text = "本週 Issue 狀態彙整"
        if len(issue_chunks) > 1:
            title_text += f" ({chunk_idx + 1}/{len(issue_chunks)})"
            
        t_header_id = f"table_title_{chunk_idx + 1}"
        requests.append({
            'createShape': {
                'objectId': t_header_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': table_slide_id,
                    'size': {'width': {'magnitude': 640, 'unit': 'PT'}, 'height': {'magnitude': 40, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 40, 'translateY': 20, 'unit': 'PT'}
                }
            }
        })
        requests.append({
            'insertText': {'objectId': t_header_id, 'text': title_text, 'insertionIndex': 0}
        })
        requests.append({
            'updateTextStyle': {
                'objectId': t_header_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Microsoft JhengHei',
                    'fontSize': {'magnitude': 22, 'unit': 'PT'},
                    'bold': True,
                    'foregroundColor': {'opaqueColor': {'rgbColor': color_navy}}
                },
                'fields': 'fontFamily,fontSize,bold,foregroundColor'
            }
        })
        
        # Add Table
        table_id = f"table_obj_{chunk_idx + 1}"
        rows_count = len(chunk) + 1
        cols_count = 6
        requests.append({
            'createTable': {
                'objectId': table_id,
                'elementProperties': {
                    'pageObjectId': table_slide_id,
                    'size': {'width': {'magnitude': 640, 'unit': 'PT'}, 'height': {'magnitude': rows_count * 25 + 30, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 40, 'translateY': 70, 'unit': 'PT'}
                },
                'rows': rows_count,
                'columns': cols_count
            }
        })
        
        headers = ["ID", "類型", "主旨", "狀態", "負責人", "專案名稱"]
        for col_idx, text in enumerate(headers):
            requests.append({
                'insertText': {
                    'objectId': table_id,
                    'cellLocation': {'rowIndex': 0, 'columnIndex': col_idx},
                    'text': text,
                    'insertionIndex': 0
                }
            })
            requests.append({
                'updateTableCellProperties': {
                    'objectId': table_id,
                    'tableRange': {'location': {'rowIndex': 0, 'columnIndex': col_idx}, 'rowSpan': 1, 'columnSpan': 1},
                    'tableCellProperties': {
                        'tableCellBackgroundFill': {'solidFill': {'color': {'rgbColor': color_navy}}}
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
                requests.append({
                    'insertText': {
                        'objectId': table_id,
                        'cellLocation': {'rowIndex': row_idx, 'columnIndex': col_idx},
                        'text': str(val),
                        'insertionIndex': 0
                    }
                })
                requests.append({
                    'updateTableCellProperties': {
                        'objectId': table_id,
                        'tableRange': {'location': {'rowIndex': row_idx, 'columnIndex': col_idx}, 'rowSpan': 1, 'columnSpan': 1},
                        'tableCellProperties': {
                            'tableCellBackgroundFill': {'solidFill': {'color': {'rgbColor': row_bg}}}
                        },
                        'fields': 'tableCellBackgroundFill.solidFill.color'
                    }
                })
                
    # 3. Slide 3+: Individual Issue Detail Slides
    for idx, issue in enumerate(issues):
        detail_slide_id = f"slide_detail_{idx + 1}"
        requests.append({
            'createSlide': {
                'objectId': detail_slide_id
            }
        })
        
        issue_id = issue.get("id", "")
        tracker = issue.get("tracker", "Issue")
        subject = issue.get("subject", "")
        detail_slide_title = f"[{tracker}] #{issue_id}: {subject}"
        if len(detail_slide_title) > 42:
            detail_slide_title = detail_slide_title[:40] + "..."
            
        d_header_id = f"detail_title_{idx + 1}"
        requests.append({
            'createShape': {
                'objectId': d_header_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': detail_slide_id,
                    'size': {'width': {'magnitude': 640, 'unit': 'PT'}, 'height': {'magnitude': 40, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 40, 'translateY': 20, 'unit': 'PT'}
                }
            }
        })
        requests.append({
            'insertText': {'objectId': d_header_id, 'text': detail_slide_title, 'insertionIndex': 0}
        })
        requests.append({
            'updateTextStyle': {
                'objectId': d_header_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Microsoft JhengHei',
                    'fontSize': {'magnitude': 20, 'unit': 'PT'},
                    'bold': True,
                    'foregroundColor': {'opaqueColor': {'rgbColor': color_navy}}
                },
                'fields': 'fontFamily,fontSize,bold,foregroundColor'
            }
        })
        
        # Left Column Card (Round Rectangle)
        left_card_id = f"left_card_{idx + 1}"
        requests.append({
            'createShape': {
                'objectId': left_card_id,
                'shapeType': 'ROUND_RECTANGLE',
                'elementProperties': {
                    'pageObjectId': detail_slide_id,
                    'size': {'width': {'magnitude': 200, 'unit': 'PT'}, 'height': {'magnitude': 310, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 40, 'translateY': 70, 'unit': 'PT'}
                }
            }
        })
        requests.append({
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
        requests.append({
            'insertText': {'objectId': left_card_id, 'text': meta_text, 'insertionIndex': 0}
        })
        requests.append({
            'updateTextStyle': {
                'objectId': left_card_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Microsoft JhengHei',
                    'fontSize': {'magnitude': 11, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'rgbColor': color_dark_text}}
                },
                'fields': 'fontFamily,fontSize,foregroundColor'
            }
        })
        
        # Right Column Content Box
        right_box_id = f"right_box_{idx + 1}"
        requests.append({
            'createShape': {
                'objectId': right_box_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': detail_slide_id,
                    'size': {'width': {'magnitude': 425, 'unit': 'PT'}, 'height': {'magnitude': 310, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 255, 'translateY': 70, 'unit': 'PT'}
                }
            }
        })
        
        key_points = issue.get("key_points", [])
        if not key_points:
            right_text = "工作進度與實作細節：\n\n• 目前尚無詳細日誌進度記錄。"
        else:
            right_text = "工作進度與實作細節：\n\n" + "\n".join(f"• {pt}" for pt in key_points)
            
        requests.append({
            'insertText': {'objectId': right_box_id, 'text': right_text, 'insertionIndex': 0}
        })
        requests.append({
            'updateTextStyle': {
                'objectId': right_box_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Microsoft JhengHei',
                    'fontSize': {'magnitude': 11, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'rgbColor': color_dark_text}}
                },
                'fields': 'fontFamily,fontSize,foregroundColor'
            }
        })
        
    # Execute batchUpdate in chunks of 80
    batch_size = 80
    for i in range(0, len(requests), batch_size):
        chunk_reqs = requests[i:i + batch_size]
        slides_service.presentations().batchUpdate(
            presentationId=pres_id,
            body={'requests': chunk_reqs}
        ).execute()
        
    url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    print(f"SUCCESS: Google Slides weekly report generated successfully!")
    print(f"Presentation Title: {file_name}")
    print(f"Presentation ID: {pres_id}")
    print(f"Google Slides URL: {url}")

if __name__ == "__main__":
    main()
