# coding=utf-8
from flask import Flask
from flask import render_template
from flask import json, request
import docker
from docker import types
import os
import shutil

app = Flask(__name__)

_WORK_DIR = '/work_dir/nginx_php/src/project1/'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add')
def add_services():
    return render_template('add.html')


@app.route('/api/docker_get_list')
def api_docker_get_list():
    client = docker.from_env()
    all_s = {}
    for i in client.services.list():
        out_port = client.api.services({'id': i.id})[0]['Endpoint']['Spec']['Ports'][0]['PublishedPort']
        all_s[i.id] = {'name': i.name, 'port': out_port}
    return json.dumps(all_s)


@app.route('/api/docker_get_info')
def api_docker_get_info():
    sid = request.args.get('sid')
    if sid and len(sid) == 25:
        client = docker.from_env()
        try:
            serv_info = client.services.get(sid)
            return json.dumps(serv_info.tasks())
        except Exception, e:
            print e
            return '0'
        return '1'
    else:
        # 没有传东西
        return '0'


@app.route('/api/get_node_info')
def api_docker_get_node_info():
    client = docker.from_env()
    node_info = {}
    for i in client.nodes.list():
        node_info[i.id] = i.attrs['Status']['Addr']
    return json.dumps(node_info)


@app.route('/api/add_service')
def api_docker_add_service():
    r = '0'
    s_name = request.args.get('sName')
    c_num = request.args.get('cNum')
    p_name = request.args.get('pName')
    if s_name == '' or c_num == '' or p_name == '':
        return r
    # 限制最大容器数目
    s_port = int(request.args.get('sPort'))
    if int(c_num) > 40 or int(c_num) < 1:
        return r
    if s_name is not None and c_num is not None and int(c_num) > 0:
        cs = docker.from_env().services
        mode = types.ServiceMode('replicated', int(c_num))
        endpoint = types.EndpointSpec('vip', {s_port: 80})
        try:
            os.mkdir(_WORK_DIR + p_name, 0755)
            f = open(_WORK_DIR + p_name + '/index.php', 'a+')
            auto_index = '''
            <?php
                echo 'Project: {}!';
                echo '<br/>';
                echo 'Docker_iner_IP:' . $_SERVER['SERVER_ADDR'];
                echo '<br/>';
                echo 'Docker_iner_Name:' . $_SERVER['HOSTNAME'];
            ?> '''.format(p_name)
            f.write(auto_index)
            f.close()
            cs.create(image='richarvey/nginx-php-fpm:latest',
                      name=s_name, mode=mode,
                      mounts=[_WORK_DIR + p_name + ':/var/www/html:rw'], endpoint_spec=endpoint)
            r = '1'
        except Exception, e:
            print e
            r = '0'
    return r


@app.route('/api/del_service')
def api_docker_del_service():
    sid = request.args.get('sid')
    if sid and len(sid) == 25:
        client = docker.from_env()
        remove_dir = client.api.services({'id': sid})[0]['Spec']['TaskTemplate']['ContainerSpec']['Mounts'][0]['Source']
        if _WORK_DIR in remove_dir:
            # os.remove(remove_dir+'/index.php')
            shutil.rmtree(remove_dir)
        try:
            client.services.get(sid).remove()
        except Exception, e:
            print e
            return '0'
        return '1'
    else:
        # 没有传东西
        return '0'

if __name__ == '__main__':
    app.debug = True
    app.run(port=8080, host="10.21.14.10")
