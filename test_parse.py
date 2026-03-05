import fitz

def parse(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    vendor = lines[0]
    date = lines[1].replace('Invoice Date:', '').strip()

    items = []
    idx = 2
    while idx < len(lines) and 'Line Total ($)' not in lines[idx]:
        idx += 1
    idx += 1 # Skip that header
    
    while idx < len(lines) and not(lines[idx].startswith('Subtotal') or lines[idx].startswith('Total')):
        try:
            desc = lines[idx]
            qty = int(lines[idx+1])
            price = float(lines[idx+2].replace('$',''))
            items.append((desc, qty, price))
            idx += 4
        except Exception as e:
            print("Err parsing items:", e)
            break
            
    # Grab extracted total
    ext_total_str = ""
    for l in lines[::-1]:
        if l.startswith('Total:'):
            ext_total_str = l
            break
    
    extracted_total = float(ext_total_str.replace('Total:', '').replace('$', '').strip())
    print("Vendor:", vendor)
    print("Date:", date)
    print("Items:", items)
    print("Total:", extracted_total)

parse('uploads/test_invoice_correct.pdf')
