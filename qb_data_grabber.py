import requests, schedule, datetime, json, git, subprocess, os


def main():
    with open("token.txt") as f:
        token = f.read()

    with open("config.json") as f:
        config = json.load(f)

    HEADERS = {
        "Authorization": token,
        "QB-Realm-Hostname": "lowes.quickbase.com",
        "Content-Type": "application/json"
    }

    query = config['QUERY']
    # try:
    response = requests.post(config['URL'], headers=HEADERS, json=config['QUERY'], timeout=30)
    # except:

    print(f"Request was processed successfully: {response.status_code == 200}")
    try:
        result = response.json()
    except json.JSONDecodeError as e:
        print(f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M")} | Status: {response.status_code} | ERROR: Decode JSON error\n{e}')
        print(f"{response.text}")
        return
    metadata = result['metadata']
    print(metadata['totalRecords'], metadata['numRecords'])
    data = result['data']
    output_dict = {
        'ids': data,
        "date_updated": datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    }
    with open('data/qb-data.json', 'w') as f:
        json.dump(output_dict, f)

def pull_git():
#    g = git.cmd.Git('.')
#    g.pull()
    subprocess.run(['cd', '/home/studio/dashboard', '&&', 'git', 'pull'], shell=True, check=True, capture_output=True)
    subprocess.run('reboot', shell=True, check=True, capture_output=True)

if __name__ == '__main__':
    # Schedule during normal business hours
    schedule.every(12).hours.do(pull_git)
    schedule.every(3).minutes.do(main)
    while True:
        schedule.run_pending()
