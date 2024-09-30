import sys

from jira import JIRA
import getpass
import pandas as pd
from datetime import datetime


def valid_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def valid_type(type):
    if type == 'HW / FW / SW':
        return 'na'
    elif 'HW' in type:
        return 'HW'
    elif 'FW' in type:
        return 'FW'
    elif 'SW' in type:
        return 'SW'
    else:
        return 'na'


def valid_findings(critical, high, medium, low):
    if critical.isdigit() and high.isdigit() and medium.isdigit() and low.isdigit():
        return True
    return False


def get_issue_findings(comment):
    findings = comment.split('Issues found:|')[1]
    findings = findings.split('\n')
    findings[0] = findings[0].lstrip(' |').strip()
    type = valid_type(findings[0])
    critical = findings[1].split(' ')[1].strip()
    high = findings[2].split(' ')[1].strip()
    medium = findings[3].split(' ')[1].strip()
    low = findings[4].split(' ')[1].strip().rstrip('|')
    if valid_findings(critical, high, medium, low) and type != 'na':
        return [type, critical, high, medium, low, True]
    else:
        return [type, critical, high, medium, low, False]

def add_to_df(df, issue_name, status, date, findings):

    if findings[0] == 'HW':
        hw_critical = findings[1]
        hw_high = findings[2]
        hw_medium = findings[3]
        hw_low = findings[4]
        fw_critical = 0
        fw_high = 0
        fw_medium = 0
        fw_low = 0
        sw_critical = 0
        sw_high = 0
        sw_medium = 0
        sw_low = 0
    elif findings[0] == 'FW':
        hw_critical = 0
        hw_high = 0
        hw_medium = 0
        hw_low = 0
        fw_critical = findings[1]
        fw_high = findings[2]
        fw_medium = findings[3]
        fw_low = findings[4]
        sw_critical = 0
        sw_high = 0
        sw_medium = 0
        sw_low = 0
    elif findings[0] == 'SW':
        hw_critical = 0
        hw_high = 0
        hw_medium = 0
        hw_low = 0
        fw_critical = 0
        fw_high = 0
        fw_medium = 0
        fw_low = 0
        sw_critical = findings[1]
        sw_high = findings[2]
        sw_medium = findings[3]
        sw_low = findings[4]

    df.loc[len(df.index)] = [issue_name, status, date, hw_critical, hw_high, hw_medium, hw_low, fw_critical,
                             fw_high, fw_medium, fw_low, sw_critical, sw_high, sw_medium, sw_low]


df = pd.DataFrame(columns=['Issue', 'Status', 'Date','HW Critical', 'HW High', 'HW Medium', 'HW Low', 'FW Critical',
                           'FW High', 'FW Medium', 'FW Low', 'SW Critical', 'SW High', 'SW Medium', 'SW Low'])

options = {
    'server': 'https://jira.devtools.intel.com/',
    'verify': False,
}

username = input("Enter username: ")
password = getpass.getpass(f'Enter password for <{username}>: ')

jira = JIRA(
    basic_auth=(username, password),
    options=options,
)

start_date = input('Enter start date in YYYY-MM-DD format: ')

if not valid_date(start_date):
    print('Date is not in YYYY-MM-DD format')
    sys.exit(1)

end_date = input('Enter end date in YYYY-MM-DD format: ')

if not valid_date(end_date):
    print('Date is not in YYYY-MM-DD format')
    sys.exit(1)

issues_in_proj = jira.search_issues(f'project=SCS6 AND status = Closed AND resolved >= {start_date} AND resolved <= {end_date} ORDER BY resolved DESC', maxResults=1000)


for issue in issues_in_proj:
    issue_status = issue.fields.status.name
    issue_date = issue.fields.created.split('T')[0]
    comments = issue.fields.comment.comments
    issue_found = False
    for comment in comments:
        if 'Issues found:' in comment.body:
            issue_found = True
            findings = get_issue_findings(comment.body)
            if findings[5] == True:
                add_to_df(df, issue, issue_status, issue_date, findings)
            else:
                print(f'{issue} - incorrectly completed \'Issue found\' template in comment')
    if issue_found == False:
        print(f'{issue} - didn\'t find \'Issue found\' template in comment')

columns_sum = ['HW Critical', 'HW High', 'HW Medium', 'HW Low', 'FW Critical','FW High', 'FW Medium', 'FW Low',
               'SW Critical', 'SW High','SW Medium', 'SW Low']

df_sum = df[columns_sum].astype(int).sum()
critical = [df_sum['HW Critical'], df_sum['FW Critical'], df_sum['SW Critical']]
high = [df_sum['HW High'], df_sum['FW High'], df_sum['SW High']]
medium = [df_sum['HW Medium'], df_sum['FW Medium'], df_sum['SW Medium']]
low = [df_sum['HW Low'], df_sum['FW Low'], df_sum['SW Low']]

dict = {'Type': ['HW', 'FW', 'SW'],
        'Critical': critical,
        'High': high,
        'Medium': medium,
        'Low': low}

df2= pd.DataFrame(dict)

print(df)

print(df2)

with pd.ExcelWriter('Add path to save output') as writer:
     df.to_excel(writer, sheet_name='Vulns per project', index=False)
     df2.to_excel(writer, sheet_name='Summary', index=False)