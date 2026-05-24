from django.shortcuts import render
def upload_report_page(request): return render(request, 'reports/upload_report.html')
def reports_list_page(request): return render(request, 'reports/report_list.html')
