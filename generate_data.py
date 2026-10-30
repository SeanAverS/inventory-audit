import pandas as pd
import random

# sample data count
random.seed(42)

def generate_inventory_data():
    products = [
        ("SKU-1001", "Bamboo Storage Box", "Home & Kitchen", 14.50),
        ("SKU-1002", "Stainless Steel Water Bottle 32oz", "Home & Kitchen", 8.25),
        ("SKU-1003", "Organic Cotton T-Shirt (Black/L)", "Apparel", 6.00),
        ("SKU-1004", "Ergonomic Laptop Stand", "Electronics Accessories", 22.00),
        ("SKU-1005", "Resistance Workout Bands Set", "Wellness", 5.75),
        ("SKU-1006", "Aromatherapy Essential Oil Diffuser", "Home & Kitchen", 11.50),
        ("SKU-1007", "USB-C Fast Charging Cable 6ft", "Electronics Accessories", 3.20),
        ("SKU-1008", "Insulated Lunch Bag", "Home & Kitchen", 7.80),
        ("SKU-1009", "Minimalist Canvas Backpack", "Apparel", 18.50),
        ("SKU-1010", "Foam Roller for Muscle Recovery", "Wellness", 9.40),
        ("SKU-1011", "Digital Kitchen Food Scale", "Home & Kitchen", 6.50),
        ("SKU-1012", "Blue Light Blocking Glasses", "Electronics Accessories", 4.75),
    ]

    erp_rows = []
    fba_rows = []

    for sku, name, category, unit_cost in products:
        erp_qty = random.randint(50, 450)
        variance_scenario = random.choice(["match", "match", "minor_diff", "major_diff", "missing_fba"])
        
        if variance_scenario == "match":
            fba_qty = erp_qty
        elif variance_scenario == "minor_diff":
            fba_qty = erp_qty + random.choice([-3, -2, 2, 4])
        elif variance_scenario == "major_diff":
            fba_qty = erp_qty + random.choice([-25, -15, 18, 30])
        elif variance_scenario == "missing_fba":
            fba_qty = 0
        
        # missing fba chart
        erp_rows.append({
            "SKU": sku, "Product Name": name, "Category": category,
            "ERP_Quantity": erp_qty, "Unit_Cost": unit_cost
        })
        
        # non missing fba chart
        if variance_scenario != "missing_fba":
            fba_rows.append({
                "SKU": sku, "Product Name": name, "Category": category,
                "FBA_Quantity": max(0, fba_qty), "Unit_Cost": unit_cost
            })

    # add SKU only existing in Amazon FBA (untracked inbound shipment for example)
    fba_rows.append({
        "SKU": "SKU-9999", "Product Name": "Mystery Promo Bundle (Discontinued)",
        "Category": "Wellness", "FBA_Quantity": 45, "Unit_Cost": 5.00
    })

    df_erp = pd.DataFrame(erp_rows)
    df_fba = pd.DataFrame(fba_rows)

    df_erp.to_csv("erp_inventory.csv", index=False)
    df_fba.to_csv("fba_inventory.csv", index=False)
    
    print("Successfully generated sample datasets: erp_inventory.csv and fba_inventory.csv")

if __name__ == "__main__":
    generate_inventory_data()