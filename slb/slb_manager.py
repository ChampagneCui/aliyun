from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

import json
import os
import sys

from enum import Enum


def byte_to_json(response):
    response_str = str(response, encoding='utf-8')
    response_json = json.loads(response_str)
    return response_json


class SlbManagerInfo():
    def __init__(self, exit_code=0, exit_message=""):
        self.exit_code = exit_code
        self.exit_message = exit_message
        self.extra_message = {}

    def __str__(self):
        return str(self.__dict__)


class SlbManager():
    """
        阿里云负载均衡管理，支持对默认的组和虚拟服务器组的管理
    """

    def __init__(self, slb_config_file, region_id="cn-beijing"):
        """
        初始化client,slb_config_file内容为以下格式
        {
            "slb_ak":"xxxxxxxxxxxxxx",
            "slb_sk":"xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        }
        """
        self.slb_config_file = slb_config_file
        self.region_id = region_id

        self.slb_manager_info = SlbManagerInfo()

        self.ak, self.sk = self.get_aksk_from_config_file()
        self.client = AcsClient(self.ak, self.sk, self.region_id)
    def pre_check(self):
        if isinstance(self.weight,int):
            if (self.weight >100 or self.weight <0):
                self.slb_manager_info.exit_code = 1
                self.slb_manager_info.exit_message = "权重设置不符合要求（0=100）" + "你的设置为" +str(self.weight)
        else:
            self.slb_manager_info.exit_code = 2
            self.slb_manager_info.exit_message = "权重不是int的，请检查"
    def set_comm_request(self, request, product_type="slb"):
        request.set_accept_format('json')
        request.set_method('POST')
        request.set_domain(product_type + '.aliyuncs.com')

    def get_aksk_from_config_file(self):
        if not (os.path.exists(self.slb_config_file)):
            self.slb_manager_info.exit_code = 1
            self.slb_manager_info.exit_message = self.slb_config_file + "文件找不到"
        try:
            with open(self.slb_config_file, 'r') as f:
                slb_config = json.load(f)
        except IOError as e:
            self.slb_manager_info.exit_code = 2
            self.slb_manager_info.exit_message = "文件读取失败" + str(e)
        return slb_config["slb_ak"], slb_config["slb_sk"]

    def get_slb_id(self):
        request = CommonRequest()
        self.set_comm_request(request)
        request.set_version('2014-05-15')
        request.set_action_name('DescribeLoadBalancers')
        request.add_query_param('LoadBalancerName', self.slb_name)
        response = self.client.do_action_with_exception(request)
        response_json = byte_to_json(response)
        if response_json["TotalCount"] != 1 :
            self.slb_manager_info.exit_code = 3
            self.slb_manager_info.exit_message ="根据负载均衡名字获取到的总个数不为1 ，请确认负载的名字，真实获取的个数为" +str(response_json["TotalCount"] )
        else:
            self.slb_id = response_json["LoadBalancers"]["LoadBalancer"][0]["LoadBalancerId"]
        a=1
    def get_ecs_id(self):
        request = CommonRequest()
        self.set_comm_request(request, product_type='ecs')
        request.set_version('2014-05-26')
        request.set_action_name('DescribeInstances')
        request.add_query_param('InstanceNetworkType', 'vpc')
        private_ip=[]
        private_ip.append(self.ecs_ip)
        request.add_query_param('PrivateIpAddresses', private_ip)
        #request.add_query_param('InstanceName', self.ecs_name)
        response = self.client.do_action_with_exception(request)
        response_json = byte_to_json(response)
        if response_json["TotalCount"] != 1 :
            self.slb_manager_info.exit_code = 4
            self.slb_manager_info.exit_message = "获取不到ecsid,请检查ecs_ip"
        else:
            self.ecs_id = response_json["Instances"]["Instance"][0]["InstanceId"]

    def set_weight_for_ecs(self):
        for backend_server in self.backend_servers:
            backend_server["ServerId"] = backend_server["VmName"]
            if backend_server["VmName"] == self.ecs_id:
                # 保留下设置前的权重
                self.slb_manager_info.extra_message["old_weight"] = backend_server["Weight"]
                backend_server["Weight"] = self.weight

    def set_weight_for_default_group_backend_servers(self):
        request = CommonRequest()
        self.set_comm_request(request)
        request.set_version('2014-05-15')
        request.set_action_name('SetBackendServers')
        request.add_query_param('LoadBalancerId', self.slb_id)
        request.add_query_param('BackendServers', self.backend_servers)
        response = self.client.do_action_with_exception(request)
        response_json = byte_to_json(response)
        # 这个貌似没法对结果进行判定。

    def set_weight_for_virtual_group_backend_servers(self):
        request = CommonRequest()
        self.set_comm_request(request)
        request.set_version('2014-05-15')
        request.set_action_name('SetVServerGroupAttribute')
        request.add_query_param('LoadBalancerId', self.slb_id)
        request.add_query_param('VServerGroupId', self.virtual_group_id)
        # request.add_query_param('VServerGroupName', 'test2')
        request.add_query_param('BackendServers', self.backend_servers)
        response = self.client.do_action_with_exception(request)
        response_json = byte_to_json(response)
        # 这个貌似没法对结果进行判定。

    def get_slb_info(self):
        request = CommonRequest()
        self.set_comm_request(request)
        request.set_version('2014-05-15')
        request.set_action_name('DescribeLoadBalancersRelatedEcs')
        request.add_query_param('LoadBalancerId', self.slb_id)
        response = self.client.do_action_with_exception(request)
        response_json = byte_to_json(response)
        if not response_json["Success"]:
            self.slb_manager_info.exit_code = 4
            self.slb_manager_info.exit_message = response_json["Message"]
        else:
            self.slb_info = response_json["LoadBalancers"]["LoadBalancer"][0]

        if self.is_default_group:
            self.backend_servers = self.slb_info["BackendServers"]["BackendServer"]
        else:
            self.virtual_server_group= None
            for virtual_group in self.slb_info["VServerGroups"]["VServerGroup"]:
                if virtual_group["GroupName"] == self.group_name:
                    self.virtual_server_group = virtual_group
                    break
            if self.virtual_server_group is None:
                self.slb_manager_info.exit_code = 6
                self.slb_manager_info.exit_message = "你输入的虚拟服务器组，不在特定的负载均衡下，请检查"
            else:
                self.virtual_group_id = self.virtual_server_group["GroupId"]
                self.backend_servers = self.virtual_server_group["BackendServers"]["BackendServer"]

        # self.backend_servers =  response_json["LoadBalancers"]["LoadBalancer"][0]["VServerGroups"]["VServerGroup"][0]["BackendServers"]["BackendServer"]

    def set_weight_for_default_group(self, slb_name, ecs_ip, weight):
        # set
        self.slb_name = slb_name
        self.ecs_ip = ecs_ip
        self.weight = weight
        self.is_default_group = True
        if self.slb_manager_info.exit_code == 0:
            self.pre_check()
        if self.slb_manager_info.exit_code == 0:
            self.get_slb_id()
        if self.slb_manager_info.exit_code == 0:
            self.get_ecs_id()

        if self.slb_manager_info.exit_code == 0:
            self.get_slb_info()

        if self.slb_manager_info.exit_code == 0:
            self.set_weight_for_ecs()

        if self.slb_manager_info.exit_code == 0:
            self.set_weight_for_default_group_backend_servers()
        return self.slb_manager_info.exit_code

    def set_weight_for_virtual_group(self, slb_name, group_name, ecs_ip, weight):
        # set
        self.slb_name = slb_name
        self.ecs_ip = ecs_ip
        self.group_name = group_name
        self.weight = weight
        self.is_default_group = False
        if self.slb_manager_info.exit_code == 0:
            self.pre_check()
        if self.slb_manager_info.exit_code == 0:
            self.get_slb_id()
        if self.slb_manager_info.exit_code == 0:
            self.get_ecs_id()
        if self.slb_manager_info.exit_code == 0:
            self.get_slb_info()
        if self.slb_manager_info.exit_code == 0:
            self.set_weight_for_ecs()
        if self.slb_manager_info.exit_code == 0:
            self.set_weight_for_virtual_group_backend_servers()
        return self.slb_manager_info.exit_code


def main():

    """
    python3 slb_manager.py <you_slb_name> <you_group_name> <you_ecs_name> <you_ecs_weight>
    """
    '''
    slb_name = sys.argv[1]
    group_name = sys.argv[2]
    ecs_ip = sys.argv[3]
    weight = int(sys.argv[4])
    '''
    slb_name = 'slb-pr-Intranet'
    group_name = '20012'
    ecs_ip = '192.168.10.160'
    weight = 100
    slb_config_file = 'slb_config_file.txt'
    region_id = 'cn-hangzhou'
    manager = SlbManager(slb_config_file=slb_config_file, region_id=region_id)
    ret =0
    if group_name == "default":
        ret =manager.set_weight_for_default_group(slb_name, ecs_ip, weight)
    else:
        ret =manager.set_weight_for_virtual_group(slb_name, group_name, ecs_ip, weight)
    sys.exit(ret)

if __name__ == "__main__":
    main()
    # manager = SlbManager(slb_config_file=r'c:\\slbconfig',region_id='cn-beijing')
    # manager.set_weight_for_default_group('lb_tmp','aliyun_test03',10)
    # manager.set_weight_for_virtual_group('lb_tmp','test2','aliyun_test02',0)