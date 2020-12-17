#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
生成应用关系网络图工具的命令模块
@module appnet_cmd
@file appnet_cmd.py
"""

import os
import sys
import time
import traceback
import subprocess
import xlrd
from graphviz import Digraph
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.simple_xml import SimpleXml
from HiveNetLib.simple_i18n import _
from HiveNetLib.simple_console.base_cmd import CmdBaseFW
from HiveNetLib.generic import CResult
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))


__MOUDLE__ = 'appnet_cmd'  # 模块名
__DESCRIPT__ = u'生成应用关系网络图工具的命令模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.12.15'  # 发布日期


class AppNetCmd(CmdBaseFW):
    """
    生成应用关系网络图工具的处理命令
    """

    #############################
    # 构造函数，在里面增加函数映射字典
    #############################

    def _init(self, **kwargs):
        """
        实现类需要覆盖实现的初始化函数

        @param {kwargs} - 传入初始化参数字典（config.xml的init_para字典）

        @throws {exception-type} - 如果初始化异常应抛出异常
        """
        self._CMD_DEALFUN_DICT = {
            'graph': self._graph_cmd_dealfun
        }
        self._console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')

    #############################
    # 通用处理函数
    #############################
    def _cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        通用处理函数，通过cmd区别调用实际的处理函数

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取真实执行的函数
        self._prompt_obj = prompt_obj  # 传递到对象内部处理
        _real_dealfun = None  # 真实调用的函数
        if 'ignore_case' in kwargs.keys() and kwargs['ignore_case']:
            # 区分大小写
            if cmd in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd]
        else:
            # 不区分大小写
            if cmd.lower() in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd.lower()]

        # 执行函数
        if _real_dealfun is not None:
            return _real_dealfun(message=message, cmd=cmd, cmd_para=cmd_para, prompt_obj=prompt_obj, **kwargs)
        else:
            prompt_obj.prompt_print(_("'$1' is not support command!", cmd))
            return CResult(code='11404', i18n_msg_paras=(cmd, ))

    #############################
    # 实际处理函数
    #############################
    def _graph_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        生成APP网络关系图

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            # 获取参数及处理参数
            _execute_path = self._console_global_para['execute_file_path']
            _run_para = {
                'file': '',
                'formatter': 'col-list',
                'comment': 'graph',
                'outformat': 'pdf',
                'direction': 'forward',
                'trace_id': '',
                'display_no_trace': 'false',
                'down_flow_first': 'true',
                'trace_relations': None,
                'save': '',
                'temp': os.path.join(_execute_path, 'temp'),
                'view': 'true',
                'cleanup': 'false',
                'graph_config': os.path.join(_execute_path, 'conf/graph_config.xml'),
                'template': 'default'
            }
            _in_para = self._cmd_para_to_dict(cmd_para, name_with_sign=False)
            _run_para.update(_in_para)
            if '{para}1' not in _run_para.keys():
                prompt_obj.prompt_print(_('you must give the $1 para!', 'file'))
                return CResult(code='20999')

            _run_para['file'] = _run_para['{para}1']
            if _run_para['save'] == '':
                _run_para['save'] = 'graph.pdf'

            # 样式模板信息处理
            _style_xml = SimpleXml(_run_para['graph_config'], encoding='utf-8')
            _style_dict = _style_xml.to_dict()['graphviz']['templates'].get(
                _run_para['template'], {
                    'graph': {},
                    'node': {},
                    'edge': {},
                    'edge_color': {},
                    'trace': {}
                }
            )
            # 关联关系线颜色
            _name_mapping = _style_dict['edge_color'].get('name_mapping', {})
            _use_round_color = _style_dict['edge_color'].get('use_round_color', False)
            _round_color = _style_dict['edge_color'].get(
                'round_color', '').replace(' ', '').split(',')

            # 生成关系字典
            _graph_json = self._formatter_col_list(_run_para['file'], prompt_obj=prompt_obj)

            # 处理生成调用链的情况
            _display_no_trace = _run_para['display_no_trace'] == 'true'
            if _run_para['trace_id'] != '':
                # 参与追踪的关系名
                if _run_para['trace_relations'] is None:
                    # 全部关系
                    _run_para['trace_relations'] = _graph_json['relation_name']
                else:
                    _run_para['trace_relations'] = _run_para['trace_relations'].split(',')

                # 获取追踪信息字典
                _trace_info = self._get_trace_info(
                    _graph_json, _run_para['trace_id'], _run_para['down_flow_first'] == 'true',
                    _run_para['direction'], _run_para['trace_relations']
                )
            else:
                _trace_info = {
                    'trace_id': '',
                    'up_nodes': list(),
                    'down_nodes': list(),
                    'up_edges': list(),
                    'down_edges': list()
                }

            # 调用链的颜色配置
            _attr_center_node = _style_dict.get('trace', {}).get('center_node', {})
            _attr_up_node = _style_dict.get('trace', {}).get('up_node', {})
            _attr_down_node = _style_dict.get('trace', {}).get('down_node', {})
            _attr_up_edge = _style_dict.get('trace', {}).get('up_edge', {})
            _attr_down_edge = _style_dict.get('trace', {}).get('down_edge', {})

            # 处理关系线条的颜色映射
            _relation_color = dict()
            _index = 0
            for _relation_name in _graph_json['relation_name']:
                if _relation_name in _name_mapping:
                    _relation_color[_relation_name] = _name_mapping[_relation_name]
                elif _use_round_color:
                    _color_index = _index % len(_round_color)
                    _relation_color[_relation_name] = _round_color[_color_index]
                    _index += 1
                else:
                    _relation_color[_relation_name] = ''

            # 开始处理画图
            _dot = Digraph(
                comment=_run_para['comment'], format=_run_para['outformat'], encoding='utf-8',
                directory=_run_para['temp'],
                graph_attr=_style_dict['graph'],
                node_attr=_style_dict['node'],
                edge_attr=_style_dict['edge']
            )

            # 开始画节点
            _added_rank = list()  # 已添加的分组
            for _id, _info in _graph_json['list'].items():
                if _info['rank'] != '':
                    # 有分组处理
                    if _info['rank'] not in _added_rank:
                        _added_rank.append(_info['rank'])
                        with _dot.subgraph() as _sub_dot:
                            _sub_dot.attr(rank='same')
                            for _sub_id in _graph_json['rank'][_info['rank']]:
                                # 节点颜色设置
                                if _sub_id == _trace_info['trace_id']:
                                    # 中心节点
                                    _attr = _attr_center_node
                                elif _sub_id in _trace_info['up_nodes']:
                                    _attr = _attr_up_node
                                elif _sub_id in _trace_info['down_nodes']:
                                    _attr = _attr_down_node
                                elif _display_no_trace and _trace_info['trace_id'] != '':
                                    # 不在链中且不应显示
                                    continue
                                else:
                                    _attr = {}
                                _sub_dot.node(
                                    _sub_id, label=_graph_json['list'][_sub_id]['name'], **_attr
                                )
                else:
                    # 节点颜色设置
                    if _id == _trace_info['trace_id']:
                        # 中心节点
                        _attr = _attr_center_node
                    elif _id in _trace_info['up_nodes']:
                        _attr = _attr_up_node
                    elif _id in _trace_info['down_nodes']:
                        _attr = _attr_down_node
                    elif _display_no_trace and _trace_info['trace_id'] != '':
                        # 不在链中且不应显示
                        continue
                    else:
                        _attr = {}

                    _dot.node(_id, label=_info['name'], **_attr)

            # 开始画关联线
            for _id, _info in _graph_json['list'].items():
                for _key, _list in _info.items():
                    if _key in ('name', 'rank'):
                        continue

                    # 判断颜色
                    _edge_color = _relation_color[_key]

                    for _temp_id in _list:
                        if _temp_id == '':
                            continue

                        if _run_para['direction'] == 'reverse':
                            _head_id = _temp_id
                            _tail_id = _id
                        else:
                            _head_id = _id
                            _tail_id = _temp_id

                        # 处理颜色
                        _findstr = '%s&&%s' % (_head_id, _tail_id)
                        if _findstr in _trace_info['up_edges']:
                            _attr = _attr_up_edge
                        elif _findstr in _trace_info['down_edges']:
                            _attr = _attr_down_edge
                        elif _display_no_trace and _trace_info['trace_id'] != '':
                            continue
                        else:
                            _attr = {'color': _edge_color}

                        _dot.edge(_head_id, _tail_id, **_attr)

            # 保存图片
            _dir, _filename = os.path.split(os.path.abspath(_run_para['save']))
            _filename = FileTool.get_file_name_no_ext(_filename)
            _dot.render(
                filename=_filename, directory=_dir,
                format=_run_para['outformat'], view=(_run_para['view'] == 'true'),
                cleanup=(_run_para['cleanup'] == 'true')
            )
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    #############################
    # 内部函数
    #############################

    def _exe_syscmd(self, cmd, shell_encoding='utf-8'):
        """
        执行系统命令

        @param {string} cmd - 要执行的命令
        @param {string} shell_encoding='utf-8' - 界面编码

        @return {int} - 返回执行结果
        """
        _sp = subprocess.Popen(
            cmd, close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True
        )
        # 循环等待执行完成
        _exit_code = None
        try:
            while True:
                try:
                    # 打印内容
                    _show_str = _sp.stdout.readline().decode(shell_encoding).strip()
                    if _show_str != '':
                        self._prompt_obj.prompt_print(_show_str)

                    _exit_code = _sp.poll()
                    if _exit_code is not None:
                        # 结束，打印异常日志
                        _show_str = _sp.stdout.read().decode(shell_encoding).strip()
                        if _show_str != '':
                            self._prompt_obj.prompt_print(_show_str)
                        if _exit_code != 0:
                            _show_str = _sp.stderr.read().decode(shell_encoding).strip()
                            if _show_str != '':
                                self._prompt_obj.prompt_print(_show_str)
                        break
                    # 释放一下CPU
                    time.sleep(0.01)
                except KeyboardInterrupt:
                    # 不允许取消
                    self._prompt_obj.prompt_print(_("Command Executing, can't exit execute job!"))
        except KeyboardInterrupt:
            # 遇到 Ctrl + C 退出
            pass

        # 最后返回
        if _exit_code is not None:
            if _exit_code != 0:
                # 执行错误，显示异常
                self._prompt_obj.prompt_print('%s : %d' % (
                    _("Command done, exit code"), _exit_code))
            else:
                self._prompt_obj.prompt_print('%s' % (_("Command execute done"), ))

        return _exit_code

    def _formatter_col_list(self, file: str, prompt_obj=None, **kwargs) -> dict:
        """
        col-list格式化文档

        @param {str} file - 要处理的文件路径
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示

        @returns {dict} - 返回的关系字典, list为以id为key的系统清单, rank为分组清单(显示在同一行)
            具体格式如下:
            {
                'list': {
                    'id': {
                        'name': '系统或模块名',
                        'rank': '分组名',
                        '关系名1': ['id1', 'id2', 'id3', ...],
                        '关系名2': [...],
                        ...
                    },
                    ...
                },
                'relation_name': ['关系名1', '关系名2', ...],
                'rank': {
                    'rank_name1': ['id1', 'id2', ...],
                    ...
                }
            }

        """
        _default_key = ('id', 'name', 'rank')
        # 打开文件开始逐个处理
        _wb = xlrd.open_workbook(filename=file)
        _sheet = _wb.sheets()[0]
        _nrows = _sheet.nrows  # 总行数
        _ncols = _sheet.ncols  # 总列数

        # 处理标题行
        _head = dict()  # 标题行字典，key为标题名, value为位置
        for _index in range(0, _ncols):
            _head[str(_sheet.cell(0, _index).value)] = _index

        # 处理关系名
        _relation_name = list()  # 关系名列表
        for _name in _head.keys():
            if _name not in _default_key:
                _relation_name.append(_name)

        # 遍历每行生成id和name的对照字典
        _name_dict = dict()  # key为name, value为id
        _relation = dict()  # 系统清单字典
        _rank = dict()  # 分组清单字典
        for _row in range(1, _nrows):
            _id = str(_sheet.cell(_row, _head['id']).value).strip()
            _name = _id
            if 'name' in _head:
                _name = str(_sheet.cell(_row, _head['name']).value).strip()
            _rank_name = ''
            if 'rank' in _head:
                _rank_name = str(_sheet.cell(_row, _head['rank']).value).strip()

            # 处理分组
            if _rank_name != '':
                if _rank_name in _rank:
                    _rank[_rank_name].append(_id)
                else:
                    _rank[_rank_name] = [_id, ]

            # 处理系统清单
            _name_dict[_name] = _id
            _relation[_id] = {'name': _name, 'rank': _rank_name}
            for _head_str, _index in _head.items():
                if _head_str not in _default_key:
                    _list_str = str(_sheet.cell(_row, _index).value).strip()
                    if _list_str != '':
                        _relation[_id][_head_str] = _list_str.split(',')

        # 处理关系数组中的name映射
        for _id, _para in _relation.items():
            for _key, _value in _para.items():
                if _key not in _default_key:
                    try:
                        for _index in range(len(_value)):
                            _item = _value[_index].strip()
                            if _item != '' and _item not in _relation:
                                # 需要通过name转换为id
                                _value[_index] = _name_dict[_item]
                            else:
                                _value[_index] = _item
                    except:
                        _prin_str = _(
                            'System [$1] relationship [$2] with not define system name [$3]!', _id, _key, _item
                        ) + '\n'
                        prompt_obj.prompt_print(_prin_str)
                        # 重新抛出异常
                        raise

        # 返回处理后的标准字典
        return {
            'list': _relation, 'relation_name': _relation_name, 'rank': _rank
        }

    def _get_trace_info(self, json: dict, trace_id: str, down_flow_first: bool, direction: str,
                        trace_relations: list) -> dict:
        """
        生成调用链追踪信息字典

        @param {dict} json - 关系字典，参考 '_get_trace_info' 的输出
        @param {str} trace_id - 要追踪的中心节点ID
        @param {bool} down_flow_first - 是否从下游优先查找
        @param {str} direction - 箭头方向
        @param {list} trace_relations - 参与追踪的关系名清单

        @returns {dict} - 调用链追踪信息字典
            {
                'trace_id': id,
                'up_nodes': ['id1', 'id2', ...],
                'down_nodes': ['id1', 'id2', ...],
                'up_edges': ['id1&&id2', 'id3&&id2', ...],
                'down_edges': ['id1&&id2', 'id3&&id2', ...]
            }
        """
        _dealed_nodes = [trace_id, ]  # 已经处理过的节点
        _trace_info = {
            'trace_id': trace_id,
            'up_nodes': list(),
            'down_nodes': list(),
            'up_edges': list(),
            'down_edges': list()
        }
        _forward = not(direction == 'reverse')

        # 内部定义函数 - 获取下游信息
        def get_down_info():
            _self_dealed_nodes = list()  # 获取当前函数中已处理的节点
            _node_stack = [trace_id, ]  # 待处理节点的堆栈
            while len(_node_stack) > 0:
                _id = _node_stack.pop()  # 获取最后一个元素

                if _id in _self_dealed_nodes:
                    # 已经处理过不再处理，避免循环
                    continue
                # 先将自己添加到已处理节点
                _self_dealed_nodes.append(_id)

                _down_list = list()  # 当前节点找到的所有下游节点清单
                if _forward:
                    # 正向箭头
                    for _key, _list in json['list'][_id].items():
                        if _key in ('name', 'rank') or _key not in trace_relations:
                            continue
                        # 直接把列表加入清单
                        _down_list.extend(_list)
                else:
                    # 反向箭头，要寻找列表中有当前id的节点
                    for _temp_id, _para in json['list'].items():
                        for _key, _list in _para.items():
                            if _key in ('name', 'rank') or _key not in trace_relations:
                                continue
                            if _id in _list:
                                _down_list.append(_temp_id)
                                break

                # 遍历所有下游节点清单进行处理
                for _down_id in _down_list:
                    if _down_id == '':
                        continue
                    # 处理箭头信息
                    _findstr = '%s&&%s' % (_id, _down_id)
                    if not(_findstr in _trace_info['up_edges'] or _findstr in _trace_info['down_edges']):
                        _trace_info['down_edges'].append(_findstr)
                    # 处理下游节点信息
                    if _down_id not in _dealed_nodes:
                        _trace_info['down_nodes'].append(_down_id)
                        _dealed_nodes.append(_down_id)  # 添加到全局的已处理节点
                    # 添加到遍历处理节点中
                    _node_stack.append(_down_id)

        # 内部定义函数 - 获取上游信息
        def get_up_info():
            _self_dealed_nodes = list()  # 获取当前函数中已处理的节点
            _node_stack = [trace_id, ]  # 待处理节点的堆栈
            while len(_node_stack) > 0:
                _id = _node_stack.pop()  # 获取最后一个元素

                if _id in _self_dealed_nodes:
                    # 已经处理过不再处理，避免循环
                    continue
                # 先将自己添加到已处理节点
                _self_dealed_nodes.append(_id)

                _up_list = list()  # 当前节点找到的所有上游节点清单
                if not _forward:
                    # 反向箭头
                    for _key, _list in json['list'][_id].items():
                        if _key in ('name', 'rank') or _key not in trace_relations:
                            continue
                        # 直接把列表加入清单
                        _up_list.extend(_list)
                else:
                    # 正向箭头，要寻找列表中有当前id的节点
                    for _temp_id, _para in json['list'].items():
                        for _key, _list in _para.items():
                            if _key in ('name', 'rank') or _key not in trace_relations:
                                continue
                            if _id in _list:
                                _up_list.append(_temp_id)
                                break

                # 遍历所有下游节点清单进行处理
                for _up_id in _up_list:
                    if _up_id == '':
                        continue
                    # 处理箭头信息
                    _findstr = '%s&&%s' % (_up_id, _id)
                    if not(_findstr in _trace_info['up_edges'] or _findstr in _trace_info['down_edges']):
                        _trace_info['up_edges'].append(_findstr)
                    # 处理下游节点信息
                    if _up_id not in _dealed_nodes:
                        _trace_info['up_nodes'].append(_up_id)
                        _dealed_nodes.append(_up_id)  # 添加到全局的已处理节点
                    # 添加到遍历处理节点中
                    _node_stack.append(_up_id)

        if down_flow_first:
            # 优先查找下游
            get_down_info()
            get_up_info()
        else:
            # 优先查找上游
            get_up_info()
            get_down_info()

        # 返回结果
        return _trace_info


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    # _appnet = AppNetCmd()
    # print(_appnet._formatter_col_list(
    #     os.path.join(os.path.dirname(__file__), os.path.pardir,
    #                  os.path.pardir, 'unit_test/test.xlsx')
    # ))
