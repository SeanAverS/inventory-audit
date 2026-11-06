# report financial discrepancies between erp and fba stocks, display them on spreadsheet

import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

def run_reconciliation():
    df_erp = pd.read_csv("erp_inventory.csv")
    df_fba = pd.read_csv("fba_inventory.csv")

    # catch items not in both files
    df_merged = pd.merge(df_erp, df_fba, on=["SKU", "Product Name", "Category"], how="outer")

    # fill missing item quantity with 0 (no NAN errors)
    df_merged["ERP_Quantity"] = df_merged["ERP_Quantity"].fillna(0)
    df_merged["FBA_Quantity"] = df_merged["FBA_Quantity"].fillna(0)
    
    # grab unit cost from existing item (x = ERP, y = FBA)
    df_merged["Unit_Cost"] = df_merged["Unit_Cost_x"].fillna(df_merged["Unit_Cost_y"])
    df_merged = df_merged.drop(columns=["Unit_Cost_x", "Unit_Cost_y"])

    # calculate difference in stock counts between ERP and FBA
    df_merged["Quantity_Variance"] = df_merged["ERP_Quantity"] - df_merged["FBA_Quantity"]
    df_merged["Absolute_Variance"] = df_merged["Quantity_Variance"].abs()

    # calculate financial impact of different stock counts 
    df_merged["Financial_Impact"] = df_merged["Quantity_Variance"] * df_merged["Unit_Cost"]

    # assign audit status and flag discrepancies for each SKU
    def assign_flag(row):
        if row["ERP_Quantity"] == 0: # warehouse never logged it
            return "Missing in ERP"
        elif row["FBA_Quantity"] == 0: # amazon does not have it
            return "Missing in FBA"
        elif abs(row["Quantity_Variance"]) > 5 or abs(row["Financial_Impact"]) > 100:
            return "Action Required"
        elif row["Quantity_Variance"] != 0:
            return "Minor Variance"
        else:
            return "Matched"

    df_merged["Audit_Status"] = df_merged.apply(assign_flag, axis=1)

    # sort table by highest financial impact 
    df_merged = df_merged.sort_values(by="Financial_Impact", key=abs, ascending=False).reset_index(drop=True)

    # build Excel report with openpyxl
    wb = openpyxl.Workbook()
    
    # excel tabs
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"
    ws_detailed = wb.create_sheet(title="Detailed Audit")

    # excel styling (navy theme)
    font_family = "Segoe UI"
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    title_font = Font(name=font_family, size=16, bold=True, color="1F4E78")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="595959")
    bold_font = Font(name=font_family, size=11, bold=True)
    regular_font = Font(name=font_family, size=11)
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
    )
    summary_border = Border(bottom=Side(style='double', color='1F4E78'), top=Side(style='thin', color='1F4E78'))

    # --- BUILD EXECUTIVE SUMMARY TAB ---
    ws_summary.views.sheetView[0].showGridLines = True
    ws_summary["B2"] = "Inventory Reconciliation & Variance Report"
    ws_summary["B2"].font = title_font
    ws_summary["B3"] = "ERP (Master Ledger) vs. Amazon FBA Stock Audit"
    ws_summary["B3"].font = subtitle_font

    summary_metrics = [
        ("Total SKUs Audited", len(df_merged), '#,##0'),
        ("SKUs with Discrepancies", len(df_merged[df_merged["Audit_Status"] != "Matched"]), '#,##0'),
        ("Total Absolute Unit Variance", df_merged["Absolute_Variance"].sum(), '#,##0'),
        ("Total Net Financial Exposure", df_merged["Financial_Impact"].sum(), '$#,##0.00'),
    ]

    row_start = 6
    ws_summary.cell(row=row_start, column=2, value="Metric Description").font = header_font
    ws_summary.cell(row=row_start, column=2).fill = header_fill
    ws_summary.cell(row=row_start, column=3, value="Value").font = header_font
    ws_summary.cell(row=row_start, column=3).fill = header_fill

    for idx, (label, val, num_fmt) in enumerate(summary_metrics):
        r = row_start + 1 + idx
        c_label = ws_summary.cell(row=r, column=2, value=label)
        c_val = ws_summary.cell(row=r, column=3, value=val)
        
        c_label.font = regular_font
        c_label.border = thin_border
        c_val.font = bold_font if idx == 3 else regular_font
        c_val.number_format = num_fmt
        c_val.alignment = Alignment(horizontal="right")
        c_val.border = thin_border

    # --- BUILD DETAILED AUDIT TAB ---
    ws_detailed.views.sheetView[0].showGridLines = True
    
    headers = [
        "SKU", "Product Name", "Category", "ERP Qty", 
        "FBA Qty", "Unit Cost", "Qty Variance", "Financial Impact ($)", "Audit Status"
    ]
    
    ws_detailed.append([]) 
    ws_detailed.append(headers)

    for col_num in range(1, len(headers) + 1):
        cell = ws_detailed.cell(row=2, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center" if col_num in [1, 9] else "left" if col_num <= 3 else "right")

    zebra_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    for idx, row in df_merged.iterrows():
        row_data = [
            row["SKU"], row["Product Name"], row["Category"],
            int(row["ERP_Quantity"]), int(row["FBA_Quantity"]), float(row["Unit_Cost"]),
            int(row["Quantity_Variance"]), float(row["Financial_Impact"]), row["Audit_Status"]
        ]
        ws_detailed.append(row_data)
        current_row = ws_detailed.max_row
        
        is_even = (idx % 2 == 1)
        for col_num in range(1, len(headers) + 1):
            cell = ws_detailed.cell(row=current_row, column=col_num)
            cell.font = regular_font
            cell.border = thin_border
            if is_even:
                cell.fill = zebra_fill
                
            if col_num in [4, 5, 7]:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right")
            elif col_num in [6, 8]:
                cell.number_format = '$#,##0.00'
                cell.alignment = Alignment(horizontal="right")
            elif col_num == 9:
                cell.alignment = Alignment(horizontal="center")

    # Total / Summary ERP And FBA Qty Row
    tot_row = ws_detailed.max_row + 1
    ws_detailed.cell(row=tot_row, column=1, value="Total / Summary").font = bold_font
    
    cell_erp = ws_detailed.cell(row=tot_row, column=4, value=f"=SUM(D3:D{tot_row-1})")
    cell_erp.font = bold_font
    cell_erp.number_format = '#,##0'
    cell_erp.border = summary_border

    cell_fba = ws_detailed.cell(row=tot_row, column=5, value=f"=SUM(E3:E{tot_row-1})")
    cell_fba.font = bold_font
    cell_fba.number_format = '#,##0'
    cell_fba.border = summary_border

    cell_fin = ws_detailed.cell(row=tot_row, column=8, value=f"=SUM(H3:H{tot_row-1})")
    cell_fin.font = bold_font
    cell_fin.number_format = '$#,##0.00'
    cell_fin.border = summary_border

   # --- BUILD VISUAL ANALYSIS CHART TAB ---
    ws_chart = wb.create_sheet(title="Visual Analysis")
    ws_chart.views.sheetView[0].showGridLines = True

    ws_chart["A2"] = "Visual of Financial Impact by SKU"
    ws_chart["A2"].font = title_font

    max_audit_row = ws_detailed.max_row - 1 
    
    data = Reference(ws_detailed, min_col=8, min_row=2, max_row=max_audit_row)
    cats = Reference(ws_detailed, min_col=2, min_row=3, max_row=max_audit_row)

    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Financial Impact ($) per SKU"
    chart.y_axis.title = "Financial Impact ($)"
    chart.x_axis.title = "Products"
    chart.legend = None

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)

    ws_chart.add_chart(chart, "A5")
    chart.width = 32  
    chart.height = 16 

    # --- AUTO-FIT COLUMN WIDTHS FOR ALL TABS ---
    for ws in [ws_summary, ws_detailed, ws_chart]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output_filename = "Reconciliation_Report.xlsx"
    wb.save(output_filename)
    print(f"Successfully generated {output_filename}")

if __name__ == "__main__":
    run_reconciliation()