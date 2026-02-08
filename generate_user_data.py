import pandas as pd
import random
from datetime import datetime, timedelta

def generate_transactions(user_name, filename):
    categories = ["Food", "Transport", "Rent", "Utilities", "Shopping", "Entertainment", "Investment", "Salary"]
    descriptions = {
        "Food": ["Zomato", "Swiggy", "Starbucks", "Local Grocery"],
        "Transport": ["Uber", "Ola", "Petrol Pump"],
        "Rent": ["Home Rent"],
        "Utilities": ["Electricity", "Airtel Bill", "Netflix"],
        "Shopping": ["Amazon", "Myntra"],
        "Entertainment": ["Movie", "Gaming"],
        "Investment": ["Mutual Fund", "Stock Purchase"],
        "Salary": ["Monthly Payout"]
    }

    data = []
    start_date = datetime.now() - timedelta(days=60)
    
                                         
                                  
                                         
    
    num_rows = 30
    if user_name == "alice":
        multipliers = {"Salary": 60000, "Food": 5.0, "Shopping": 3.0}
    elif user_name == "bob":
        multipliers = {"Salary": 80000, "Food": 1.0, "Investment": 10.0}
    else:
        multipliers = {"Salary": 150000, "Rent": 2.0}

    for _ in range(num_rows):
        category = random.choice(categories)
        desc = random.choice(descriptions[category])
        date = start_date + timedelta(days=random.randint(0, 60))
        
        if category == "Salary":
            amount = multipliers.get("Salary", 50000)
            tx_type = "Credit"
        else:
            amount = random.randint(100, 2000) * multipliers.get(category, 1.0)
            tx_type = "Debit"
            
        data.append([date.strftime("%Y-%m-%d"), desc, category, round(amount, 2), tx_type])
    
    df = pd.DataFrame(data, columns=["Date", "Description", "Category", "Amount", "Type"])
    df.to_csv(filename, index=False)
    print(f"Generated transactions for {user_name} at {filename}")

def generate_policy(user_name, filename):
    policies = {
        "alice": """
# Alice's Health Insurance Policy
- **Plan**: Platinum Care
- **Cardiac Coverage**: ₹15,00,000
- **Waiting Period**: 1 year
- **Maternity**: Covered after 3 years
        """,
        "bob": """
# Bob's Life Insurance Policy
- **Sum Assured**: ₹1,00,00,000
- **Term**: 30 Years
- **Critical Illness Rider**: Included
        """,
        "charlie": """
# Charlie's Combined Insurance
- **Health Coverage**: ₹25,00,000
- **Car Insurance**: Comprehensive coverage for BMW X5
- **Home Insurance**: Valid until 2026
        """
    }
    with open(filename, 'w') as f:
        f.write(policies[user_name])
    print(f"Generated policy for {user_name} at {filename}")

if __name__ == "__main__":
    for user in ["alice", "bob", "charlie"]:
        generate_transactions(user, f"../data/users/{user}/transactions.csv")
        generate_policy(user, f"../data/users/{user}/policy.md")
