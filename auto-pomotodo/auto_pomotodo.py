#!/usr/bin/env python# -*- coding: utf-8 -*-"""PyCharm : Copyright (C) 2016-2017 EINDEX Li@Author        : EINDEX Li@File          : auto_pomotodo.py@Created       : 2017/3/31@Last Modified : 2017/3/31"""from flask import Flask, request, render_templatefrom requests import Sessionimport osimport jsonimport reimport dateutil.parserapp = Flask(__name__)app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')pomotodo_key = os.getenv('POMOTODO_KEY')wunderlist_access_token = os.getenv('WUNDERLIST_ACCESS_TOKEN')wunderlist_client_id = os.getenv('WUNDERLIST_CLIENT_ID')session = Session()session.headers.update({'Authorization': f'token {pomotodo_key}',                        'X-Access-Token': wunderlist_access_token,                        'X-Client-ID': wunderlist_client_id})@app.route('/')def index():    return render_template('index.html')@app.route('/user')def user():    r = session.get('http://a.wunderlist.com/api/v1/lists')    data = json.loads(r.content.decode())    for i, item in enumerate(data):        r = session.get('http://a.wunderlist.com/api/v1/webhooks', params={'list_id': item['id']})        if json.loads(r.content.decode()):            data[i]['webhooks'] = True    return render_template('user.html', data=data)@app.route('/user/list/<id>', methods=['PUT'])def user_list(id):    if request.json['checked']:        r = session.post('http://a.wunderlist.com/api/v1/webhooks',                         params={'list_id': id,                                 'url': 'http://pomotodo.eindex.me/webhooks',                                 'processor_type': 'generic',                                 'configuration': ''})    else:        r = session.delete(f'http://a.wunderlist.com/api/v1/webhooks/{id}', params={'revision': 0})    return r.content.decode()def get_wunderlist_info(todo_id):    data = session.get(f'http://a.wunderlist.com/api/v1/tasks/{todo_id}').json()    r = session.get('http://a.wunderlist.com/api/v1/notes', params={'task_id': todo_id})    if r.ok:        data['content'] = json.loads(r.content.decode())[0]['content']    r = session.get('http://a.wunderlist.com/api/v1/reminders', params={'task_id': todo_id})    if r.ok:        data['date'] = json.loads(r.content.decode())[0]['date']    return datadef wunderlist_webhooks_json(func):    def wrapper(todo_id):        params = {}        data = get_wunderlist_info(todo_id)        if 'title' in data:            params['description'] = data['title']            re_pomo_count = re.search(r'-t[0-9]{1,}', params['description'])            if re_pomo_count:                params['description'] = ''.join([params['description'][:re_pomo_count.start()],                                                 params['description'][re_pomo_count.end():]])                params['estimated_pomo_count'] = re_pomo_count.group(0)[2:]        if 'content' in data:            params['notice'] = f"{data['content']} ${todo_id}"        else:            params['notice'] = f"${todo_id}"        if 'starred' in data:            params['pin'] = data['starred']        if 'completed' in data:            params['completed'] = data['completed']        if 'date' in data:            params['remind_time'] = dateutil.parser.parse(data['date'])        return func(todo_id=todo_id, params=params)    return wrapperdef pomo_get(todo_id):    todos = json.loads(session.get('https://api.pomotodo.com/1/todos').content.decode())    for todo in todos:        if not todo['notice']:            continue        m = r'%s' % todo_id        if re.search(m, todo['notice']):            return todo@wunderlist_webhooks_jsondef pomo_create(todo_id, params):    session.post('https://api.pomotodo.com/1/todos', params)@wunderlist_webhooks_jsondef pomo_update(todo_id, params):    todo = pomo_get(todo_id)    if todo:        session.patch(f'https://api.pomotodo.com/1/todos/{todo["uuid"]}', params)def pomo_delete(todo_id):    todo = pomo_get(todo_id)    if todo:        session.delete(f'https://api.pomotodo.com/1/todos/{todo["uuid"]}')@app.route('/webhooks', methods=['POST'])def wunderlist_webhooks():    operation = request.json['operation']    todo_id = request.json['after']['id']    if operation == 'create':        pomo_create(todo_id)    elif operation == 'update':        pomo_update(todo_id)    elif operation == 'delete':        pomo_delete(todo_id)    return 'ok'if __name__ == '__main__':    app.run(host='0.0.0.0', port=5001, debug=True)