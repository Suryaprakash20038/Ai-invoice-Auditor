from app.models import InvoiceData

def validate_invoice(invoice: InvoiceData):
    calculated_total = sum(item.quantity * item.unit_price for item in invoice.items)
    
    if abs(calculated_total - invoice.extracted_total) < 0.01:
        status = "correct"
        message = "Invoice calculations are fully correct."
    else:
        status = "error"
        message = "Mathematical discrepancy detected"
        
    return {
        "vendor": invoice.vendor,
        "date": invoice.date,
        "items": invoice.items,
        "extracted_total": invoice.extracted_total,
        "calculated_total": calculated_total,
        "status": status,
        "message": message
    }
