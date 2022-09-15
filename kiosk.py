from flask import Flask, render_template
import requests, json, os
from datetime import datetime, timedelta

app = Flask(__name__)

title = "Content Studio Kiosk"

data_path = f"{os.path.join(os.getcwd(), 'data', 'qb-data.json')}"

with open(data_path) as f:
    old_data = json.load(f)


def process_qb_data(ids):
    with open("config.json") as f:
        config = json.load(f)
    flattened_inventories = {}
    for asset_request in ids:
        if asset_request['25']['value'] not in config['ON_WHITE_COMPLEXITIES']:
            continue
        field_ids = asset_request.keys()
        values = asset_request.values()
        output_dict = dict(zip(field_ids, [x["value"] for x in values]))
        current_inventory = flattened_inventories.get(output_dict["126"], None)
        if current_inventory:
            current_inventory["25"].append(output_dict["25"])
            current_inventory["66"].append(output_dict["66"])
        else:
            flattened_inventories.update(
                {
                    output_dict['126']: {
                        "160": output_dict["160"],
                        "25": [output_dict["25"]],
                        "66": [output_dict["66"]]
                    }
                }
            )
    print(len(flattened_inventories))
    completed_inventories = []
    for inv_id, inventory in flattened_inventories.items():
        list_comp = [x for x in inventory['66'] if x in config["REJECTED_ASSET_STATUSES"]]
        # if '' in inventory['66'] or 'Video Pending' in inventory['66']:
        #     breakpoint()
        if all(list_comp):
            completed_inventories.append(int(inv_id))
        else:
            continue

    return sorted(completed_inventories)

def process_asset_requests(data):
    try:
        with open("config.json") as f:
            config = json.load(f)
        recs_in_inv_loc = [x for x in data if x['160']['value'] in config['GPS_COORDINATES']]
        #print(f'{len(recs_in_inv_loc)=}')
        on_white_complexities = [x for x in recs_in_inv_loc if x['25']['value'] in config['ON_WHITE_COMPLEXITIES']]
        #print(f'{len(on_white_complexities)=}')
        processed_records = []
        inv_id_list = []
        prev_id = None
        for item in on_white_complexities:
            id = int(item['126']['value'])
            if prev_id == id or prev_id is None:
                inv_id_list.append(item)
                prev_id = id
                continue
            else:
                # breakpoint()
                prev_id = id
                processed_records.append(inv_id_list)
                inv_id_list = [item]
        inv_ready_to_move = []
        not_ready = []
        print(f'{len(processed_records)=}')
        # breakpoint()
        with open('temp.log', 'a') as f:
            for inventory in processed_records:
                #print(f'{inventory=}')
                #print(f'{len(inventory)=}')
                error_flag = False
                if inventory[0]['126']['value'] in [x[0]['126']['value'] for x in not_ready]:
                    error_flag = True
                else:
                    for record in inventory:
                        status = record['66']['value']
                        if status not in config['ASSET_STATUSES'] or status == '':
                            error_flag = True
                            break
                f.write(f"{inventory[0]['126']['value']}|{error_flag}|{[x['66']['value'] for x in inventory]}\n")
                if not error_flag:
                    inv_ready_to_move.append(inventory)
                else:
                    not_ready.append(inventory)
            #print(f'{inv_ready_to_move=}')
            #print(f'{not_ready=}')
            return inv_ready_to_move, not_ready
    except Exception as e:
        print(e)
        raise Exception(e)

@app.route("/")
def hello_world():
    try:
        with open(data_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(e)
        data = old_data
    updated = datetime.strptime(data['date_updated'], "%Y/%m/%d %H:%M")
    if datetime.now() - timedelta(hours=1) > updated:
        bg_color = "bg-danger"
    else:
        bg_color = "bg-light"
    inventory_ids = process_qb_data(data['ids'])
    # inventory_ids = [int(asset[0]['126']['value']) for asset in good_to_go_inv]
    # inventory_ids.sort()
    # not_complete = [int(asset[0]['126']['value']) for asset in not_good_to_go]
    # not_complete.sort()
    return render_template(
        'layout.html',
        title=title,
        ids=sorted(set(inventory_ids)),
        date_updated=data['date_updated'],
        background_color=bg_color)
        #, not_complete=sorted(set(not_complete)))