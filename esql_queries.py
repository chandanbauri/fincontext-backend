"""
This file contains ES|QL (Elasticsearch SQL) templates for the 'Transaction Calculator' tool.
In Phase 3, when you set up 'Tool B' in the Kibana Agent Builder, you can use these 
logic patterns to answer user questions about money.
"""

                                         
QUERY_EXPENSES_BY_CATEGORY = """
FROM fincontext-transactions
| WHERE Type == "Debit"
| STATS total_amount = SUM(Amount) BY Category
| SORT total_amount DESC
"""

                                     
QUERY_LARGE_TRANSACTIONS = """
FROM fincontext-transactions
| WHERE Amount > 1000
| SORT Date DESC
| LIMIT 5
"""

                        
QUERY_MONTHLY_TREND = """
FROM fincontext-transactions
| EVAL month = DATE_TRUNC(1 month, Date)
| STATS monthly_spend = SUM(Amount) BY month, Type
| SORT month ASC
"""

                                                  
QUERY_MERCHANT_SEARCH = """
FROM fincontext-transactions
| WHERE Description LIKE "%Zomato%"
| STATS total = SUM(Amount), count = COUNT(*)
"""

def get_esql_example(query_type):
    if query_type == "expenses":
        return QUERY_EXPENSES_BY_CATEGORY
    elif query_type == "trend":
        return QUERY_MONTHLY_TREND
    return "Query type not found."

if __name__ == "__main__":
    print("ES|QL Query for total expenses:")
    print(QUERY_EXPENSES_BY_CATEGORY)
