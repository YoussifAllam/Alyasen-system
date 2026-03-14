from datetime import date
from typing import List, Dict, Any, Callable

from django.db.models import Sum, Value, Count
from django.db.models.fields import DecimalField
from django.db.models.functions import Coalesce

import concurrent.futures
from django.db import connection

from apps.Expenses.models import Expenses
from apps.Suppliers.models import InvoicePayment
from apps.Workers.models import WorkersPaidSalary
from apps.Clients.models import ClientInvoice
from apps.SegmentalSallling.models import Invoice


def get_expenses_report(start_date: date, end_date: date) -> float:
    result = Expenses.objects.filter(created_date__range=[start_date, end_date]).aggregate(
        total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
    )
    return result["total"]


def get_suppliers_payment_report(start_date: date, end_date: date) -> float:
    result = InvoicePayment.objects.filter(payment_date__range=[start_date, end_date]).aggregate(
        total=Coalesce(Sum("payment_amount"), Value(0), output_field=DecimalField())
    )
    return result["total"]


def get_salaries_report(start_date: date, end_date: date) -> float:
    result = WorkersPaidSalary.objects.filter(paid_date__range=[start_date, end_date]).aggregate(
        total=Coalesce(Sum("paid_amount"), Value(0), output_field=DecimalField())
    )
    return result["total"]


def get_sells_process_num_report(start_date: date, end_date: date) -> int:
    result = ClientInvoice.objects.filter(invoice_date__range=[start_date, end_date]).aggregate(
        total=Count("id")
    )

    return result["total"]


def get_sells_amount_report(start_date: date, end_date: date) -> float:
    result = ClientInvoice.objects.filter(invoice_date__range=[start_date, end_date]).aggregate(
        total=Coalesce(Sum("invoice_total_amount"), Value(0), output_field=DecimalField())
    )

    return result["total"]


def get_segmental_sells_amount_report(start_date: date, end_date: date) -> float:
    result = Invoice.objects.filter(invoice_date__range=[start_date, end_date]).aggregate(
        total=Coalesce(Sum("invoice_total_amount"), Value(0), output_field=DecimalField())
    )

    return result["total"]


# Maps report keys to their corresponding generator functions
REPORT_GENERATORS: Dict[str, Callable[[date, date], Any]] = {
    "expenses_report": get_expenses_report,
    "suppliers_payment_report": get_suppliers_payment_report,
    "salaries_report": get_salaries_report,
    "sells_process_num_report": get_sells_process_num_report,
    "sells_amount_report": get_sells_amount_report,
    "segmental_sells_amount_report": get_segmental_sells_amount_report,
}


def _execute_and_close_connection(report_function, start_date, end_date):
    """
    A wrapper function to ensure each thread properly closes its
    database connection. This is a crucial best practice for Django.
    """
    try:
        return report_function(start_date, end_date)
    finally:
        connection.close()


def get_reports(start_date: date, end_date: date, requested_reports: List[str]) -> Dict[str, Any]:
    """
    Generates reports by running their database queries concurrently in a thread pool.
    The total execution time will be close to the time of the single slowest query.
    """
    reports = {}

    # Use a ThreadPoolExecutor to manage a pool of worker threads.
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # { 'expenses_report': <Future object>, 'salaries_report': <Future object> }
        future_to_report = {}

        for report_key in requested_reports:
            if generator_func := REPORT_GENERATORS.get(report_key):
                # Schedule the function to be executed in a thread.
                # The _execute_and_close_connection wrapper is used for safety.
                future = executor.submit(_execute_and_close_connection, generator_func, start_date, end_date)
                future_to_report[report_key] = future

        # As each future completes, get its result.
        for report_key, future in future_to_report.items():
            try:
                # The .result() method waits for the thread to finish and returns its value.
                reports[report_key] = future.result()
            except Exception as e:
                # Handle potential errors from any of the report functions
                print(f"\n Error generating report '{report_key}': {e}")
                reports[report_key] = "Error"

    return reports
