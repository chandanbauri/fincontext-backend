import csv
import random
from datetime import datetime, timedelta

def generate_bank_transactions(filename, num_rows=100):
    categories = ["Food", "Transport", "Rent", "Utilities", "Shopping", "Entertainment", "Investment", "Salary"]
    descriptions = {
        "Food": ["Zomato", "Swiggy", "Starbucks", "Local Grocery", "Whole Foods"],
        "Transport": ["Uber", "Ola", "Gas Station", "Train Ticket"],
        "Rent": ["Property Management", "Landlord Payment"],
        "Utilities": ["Electricity Bill", "Water Bill", "Internet", "Mobile Recharge"],
        "Shopping": ["Amazon", "Myntra", "H&M", "Decathlon"],
        "Entertainment": ["Netflix", "Movie Theater", "Spotify", "Gaming"],
        "Investment": ["PPF Deposit", "Mutual Fund SIP", "Stock Purchase"],
        "Salary": ["Employer Monthly Salary"]
    }

    start_date = datetime.now() - timedelta(days=90)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Category", "Amount", "Type"])
        
        for _ in range(num_rows):
            category = random.choice(categories)
            desc = random.choice(descriptions[category])
            date = start_date + timedelta(days=random.randint(0, 90))
            
            if category == "Salary":
                amount = random.randint(50000, 150000)
                tx_type = "Credit"
            else:
                amount = random.randint(10, 5000)
                tx_type = "Debit"
                
            writer.writerow([date.strftime("%Y-%m-%d"), desc, category, amount, tx_type])

def generate_dummy_insurance_policy(filename):
    content = """
# Reliance Health Insurance Policy - Silver Plan
**Policy Holder:** John Doe
**Policy Number:** H-123456789
**Coverage Period:** Jan 2024 - Jan 2025

## Coverage Details:
1. **Cardiac Care:** Coverage up to ₹5,00,000 for any cardiac-related procedures after a 2-year waiting period.
2. **Accident Hospitalization:** Immediate coverage up to ₹10,00,000.
3. **Maternity:** Not covered in Silver Plan.
4. **Day Care Procedures:** Over 500+ procedures covered.
5. **No Claim Bonus:** 10% increase in sum insured for every claim-free year.

## Waiting Periods:
- 30 days for initial illness.
- 2 years for specific ailments like Cataract, Hernia, and Cardiac issues.
- 4 years for Pre-existing diseases.

## Contact Information:
For claims, call 1800-XXX-XXXX or email claims@reliancehealth.com
    """
    with open(filename, mode='w') as file:
        file.write(content)

if __name__ == "__main__":
    generate_bank_transactions("fincontext/data/structured/bank_statement.csv")
    generate_dummy_insurance_policy("fincontext/data/unstructured/health_insurance_policy.md")
    print("Dummy data generated in fincontext/data/")
