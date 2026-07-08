# /// script
# dependencies = [
#     "pywin32",
# ]
# ///

import os
import sys
import json
from datetime import datetime

def RGB(r, g, b):
    return r + (g << 8) + (b << 16)

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run generate_weekly_report.py <json_path>")
        sys.exit(1)
        
    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found: {json_path}")
        sys.exit(1)
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    issues = data.get("issues", [])
    
    # Connect to PowerPoint
    import win32com.client
    try:
        ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
    except Exception:
        try:
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True
        except Exception as e:
            print(f"Error: Failed to launch PowerPoint: {e}")
            sys.exit(1)
            
    # Get active presentation or create a new one
    try:
        pres = ppt_app.ActivePresentation
    except Exception:
        # No presentation is open, create from the Mirle template
        template_path = r"C:\Users\yucheng\Documents\自訂 Office 範本\盟立集團-新版ppt-2.potx"
        if os.path.exists(template_path):
            pres = ppt_app.Presentations.Open(template_path)
        else:
            print(f"Warning: Template not found at {template_path}. Creating blank presentation.")
            pres = ppt_app.Presentations.Add()
            
    # We must have at least 3 slides in the template to copy the layout. 
    # Slide 3 uses layout '3_自訂版面配置' which is our clean content layout.
    if pres.Slides.Count < 3:
        print("Error: The active presentation must have at least 3 slides to extract layout templates.")
        sys.exit(1)
        
    # Get layout from Slide 3
    content_layout = pres.Slides(3).CustomLayout
    
    # Delete Slide 2 and subsequent slides (retaining only Slide 1)
    for i in range(pres.Slides.Count, 1, -1):
        try:
            pres.Slides(i).Delete()
        except Exception as e:
            print(f"Warning: Failed to delete slide {i}: {e}")
            
    # 1. Update Title Slide (Slide 1)
    title_slide = pres.Slides(1)
    title_shape = None
    subtitle_shape = None
    for i in range(1, title_slide.Shapes.Count + 1):
        shape = title_slide.Shapes(i)
        if shape.Top < 200:
            title_shape = shape
        else:
            subtitle_shape = shape
            
    if title_shape:
        title_shape.TextFrame.TextRange.Text = "盟立集團 工作週報"
        title_shape.TextFrame.TextRange.Font.Name = "Microsoft JhengHei"
        title_shape.TextFrame.TextRange.Font.Bold = True
        
    if subtitle_shape:
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        subtitle_shape.TextFrame.TextRange.Text = f"報告期間：{start_date} ~ {end_date}\n產出時間：{current_date_str}\n報告人員：機器人開發小組"
        subtitle_shape.TextFrame.TextRange.Font.Name = "Microsoft JhengHei"
        subtitle_shape.TextFrame.TextRange.Font.Size = 14
        
    # 2. Add Issue Table Slide(s)
    # Chunk issues by 10 to fit onto single slides
    chunk_size = 10
    issue_chunks = [issues[i:i + chunk_size] for i in range(0, len(issues), chunk_size)]
    
    for chunk_idx, chunk in enumerate(issue_chunks):
        # Add slide
        slide_idx = pres.Slides.Count + 1
        table_slide = pres.Slides.AddSlide(slide_idx, content_layout)
        
        # Set Title
        title_text = "本週 Issue 狀態彙整"
        if len(issue_chunks) > 1:
            title_text += f" ({chunk_idx + 1}/{len(issue_chunks)})"
            
        title_placeholder = table_slide.Shapes("Title 1")
        title_placeholder.TextFrame.TextRange.Text = title_text
        title_placeholder.TextFrame.TextRange.Font.Name = "Microsoft JhengHei"
        
        # Add Table
        rows_count = len(chunk) + 1
        cols_count = 6
        table_shape = table_slide.Shapes.AddTable(rows_count, cols_count, 50, 120, 860, rows_count * 25 + 30)
        table = table_shape.Table
        
        # Set Column Widths (total 860)
        widths = [60, 80, 340, 80, 100, 200]
        for col_idx, w in enumerate(widths, 1):
            table.Columns(col_idx).Width = w
            
        # Headers
        headers = ["ID", "類型", "主旨", "狀態", "負責人", "專案名稱"]
        for col_idx, text in enumerate(headers, 1):
            cell = table.Cell(1, col_idx)
            cell.Shape.TextFrame.TextRange.Text = text
            cell.Shape.TextFrame.TextRange.Font.Bold = True
            cell.Shape.TextFrame.TextRange.Font.Size = 13
            cell.Shape.TextFrame.TextRange.Font.Name = "Microsoft JhengHei"
            cell.Shape.TextFrame.VerticalAnchor = 3  # Middle
            cell.Shape.TextFrame.TextRange.ParagraphFormat.Alignment = 2 if col_idx in [1, 2, 4, 5] else 1
            
        # Row Data
        for row_idx, issue in enumerate(chunk, 2):
            # Issue data map
            row_data = [
                str(issue.get("id", "")),
                issue.get("tracker", ""),
                issue.get("subject", ""),
                issue.get("status", ""),
                issue.get("assignee", "") or "未指派",
                issue.get("project", "")
            ]
            
            for col_idx, val in enumerate(row_data, 1):
                cell = table.Cell(row_idx, col_idx)
                cell.Shape.TextFrame.TextRange.Text = val
                cell.Shape.TextFrame.TextRange.Font.Size = 11
                cell.Shape.TextFrame.TextRange.Font.Name = "Microsoft JhengHei"
                cell.Shape.TextFrame.VerticalAnchor = 3  # Middle
                cell.Shape.TextFrame.TextRange.ParagraphFormat.Alignment = 2 if col_idx in [1, 2, 4, 5] else 1
                
    # 3. Add Individual Detail Slides
    for issue in issues:
        slide_idx = pres.Slides.Count + 1
        detail_slide = pres.Slides.AddSlide(slide_idx, content_layout)
        
        # Set Title
        title_placeholder = detail_slide.Shapes("Title 1")
        issue_id = issue.get("id", "")
        tracker = issue.get("tracker", "Issue")
        subject = issue.get("subject", "")
        detail_slide_title = f"[{tracker}] #{issue_id}: {subject}"
        
        # Truncate if extremely long to fit header
        if len(detail_slide_title) > 40:
            detail_slide_title = detail_slide_title[:38] + "..."
            
        title_placeholder.TextFrame.TextRange.Text = detail_slide_title
        title_placeholder.TextFrame.TextRange.Font.Name = "Microsoft JhengHei"
        
        # Add Left Column - Rounded Rectangle
        left_rect = detail_slide.Shapes.AddShape(5, 50, 120, 260, 350)  # msoShapeRoundedRectangle = 5
        left_rect.Fill.Solid()
        left_rect.Fill.ForeColor.RGB = RGB(247, 250, 252)  # Light gray-blue
        left_rect.Line.Visible = False
        
        # Configure textframe margins
        tf_left = left_rect.TextFrame
        tf_left.MarginLeft = 15
        tf_left.MarginTop = 15
        tf_left.MarginRight = 15
        tf_left.MarginBottom = 15
        tr_left = tf_left.TextRange
        tr_left.Text = ""
        
        def add_meta_field(text_range, label, value):
            p_label = text_range.InsertAfter(label + "\n")
            p_label.Font.Bold = True
            p_label.Font.Size = 13
            p_label.Font.Color.RGB = RGB(26, 54, 93)  # Dark blue
            p_label.Font.Name = "Microsoft JhengHei"
            p_label.ParagraphFormat.Alignment = 1  # Left
            
            p_val = text_range.InsertAfter(value + "\n\n")
            p_val.Font.Bold = False
            p_val.Font.Size = 13
            p_val.Font.Color.RGB = RGB(74, 85, 104)  # Gray
            p_val.Font.Name = "Microsoft JhengHei"
            p_val.ParagraphFormat.Alignment = 1  # Left
            
        add_meta_field(tr_left, "專案名稱", issue.get("project", ""))
        add_meta_field(tr_left, "目前狀態", issue.get("status", ""))
        add_meta_field(tr_left, "負責人員", issue.get("assignee", "") or "未指派")
        add_meta_field(tr_left, "建立日期", issue.get("created_on", "")[:10])
        
        # Add Right Column - Text Box for bullet points
        right_box = detail_slide.Shapes.AddTextbox(1, 340, 120, 570, 350)  # msoTextOrientationHorizontal = 1
        tf_right = right_box.TextFrame
        tf_right.WordWrap = True
        tf_right.MarginLeft = 10
        tf_right.MarginTop = 10
        tr_right = tf_right.TextRange
        
        # Add right column title
        tr_right.Text = "工作進度與實作細節：\n"
        tr_right.Font.Name = "Microsoft JhengHei"
        tr_right.Font.Bold = True
        tr_right.Font.Size = 16
        tr_right.Font.Color.RGB = RGB(26, 54, 93)  # Dark blue
        
        key_points = issue.get("key_points", [])
        if not key_points:
            p_empty = tr_right.InsertAfter("• 目前尚無詳細日誌進度記錄。\n")
            p_empty.Font.Bold = False
            p_empty.Font.Size = 14
            p_empty.Font.Color.RGB = RGB(113, 128, 150)
            p_empty.Font.Name = "Microsoft JhengHei"
            p_empty.ParagraphFormat.SpaceAfter = 6
        else:
            for pt in key_points:
                p_pt = tr_right.InsertAfter(f"• {pt}\n")
                p_pt.Font.Bold = False
                p_pt.Font.Size = 13
                p_pt.Font.Color.RGB = RGB(45, 55, 72)  # Dark charcoal
                p_pt.Font.Name = "Microsoft JhengHei"
                p_pt.ParagraphFormat.SpaceAfter = 6
                
    print("PowerPoint weekly report generated successfully.")

if __name__ == "__main__":
    main()
