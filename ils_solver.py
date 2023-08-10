from copy import *
import random
import sys
import os
from operator import itemgetter
from queue import Queue
from math import log
import signal
import time

# Problem related parameters
node_type_selection_probability = {'subtree': 10, 'internal': 10, 'leaf': 10, 'leafs': 10, 'root': 10,'top': 10, 'bottom': 10, 'level': 10, 'path': 10, 'partial_path': 10, 'partial_path_bottom': 0}
random_walk_limit = 0.9
sub_tree_size_probability = 0.8
top_max_limit_probability = 0.8
bottom_depth_max_limit_probability = 0.05

# Instance selection
instance_type = 'heur'
start_instance_index = 1
end_instance_index = start_instance_index + 1
recursion_limit = 100000000


class Killer:
    exit_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum, frame):
        self.exit_now = True


class Solution:
    def __init__(self, _root, _representation, _fitness):
        self.root = _root
        self.representation = copy(_representation)
        self.fitness = _fitness


class IteratedLocalSearch:
    def __init__(self, file_name):
        self.n_list = list()
        self.e_list = list()
        self.adjacency_list, n_nodes, n_edges = self.get_adjacency_list(
            file_name)
        self.n_nodes = n_nodes
        self.n_edges = n_edges
        self.number_of_iterations = 50000
        self.number_of_iterations_with_no_improvement = 250
        self.number_of_tweaks = 10
        self.tabu_list_length_probability = 0.0
        self.fully_random_initial_solution = False
        self.perturbed_solution_deprecation_percentage = 0.7
        self.insert_nodes_in_initial_solution_descending_order = True
        self.insert_nodes_in_random_order = False
        self.insert_nodes_in_descending_order = True
        self.max_number_of_paths = 50
        self.max_number_of_paths_list = [30, 40, 50, 60, 70, 80, 90, 100]
        self.max_partial_path_length_percentage = 0.9
        self.minimal_perturb_intensity = int(
            1.5 * log(self.n_nodes * self.n_edges, 2))
        self.terminate_without_improvement_iterations = 10000
        if self.fully_random_initial_solution:
            self.number_of_edges_list = random.sample(
                range(0, self.n_nodes), self.n_nodes)
        else:
            self.number_of_edges_list = self.create_number_of_edges_list()
        self.tabu_list = {}

        #  30min change

    def ils_algorithm(self):
        start_time = time.time()  # Start time
        killer = Killer()
        current = self.get_initial_solution()
        best = copy(current)
        iteration_counter = 1
        iteration_no_improvement_counter = 1

        while True:  # Change the loop condition
            tweak_counter = 1
            current_tweak = copy(current)
            new_solution_node_list = list()
            while tweak_counter <= self.number_of_tweaks:
                selected_nodes, node_type = self.select_nodes(
                    current_tweak, iteration_counter)
                new_solution = self.move_node(
                    current_tweak, selected_nodes, node_type)
                if new_solution.fitness <= current_tweak.fitness:
                    current_tweak = copy(new_solution)
                    new_solution_node_list = selected_nodes
                tweak_counter += 1
            current = copy(current_tweak)
            # print("current fitness: ", current.fitness)
            for used_node in new_solution_node_list:
                if used_node in current.representation[current.root]:
                    used_node_parent = current.root
                else:
                    used_node_parent = self.find_non_root_parent_node(
                        current.representation, used_node)
                tabu_feature = str(used_node) + '-' + str(used_node_parent)
                self.tabu_list[tabu_feature] = iteration_counter
            if current.fitness < best.fitness:
                best = copy(current)
                iteration_no_improvement_counter = 0
                self.max_number_of_paths = 50
            else:
                iteration_no_improvement_counter += 1
            if iteration_no_improvement_counter % self.number_of_iterations_with_no_improvement == 0:
                current = self.perturb(
                    best, iteration_counter, iteration_no_improvement_counter)
                # insert_nodes_in_random_order = not insert_nodes_in_random_order
                # insert_nodes_in_descending_order = not insert_nodes_in_descending_order
                self.max_number_of_paths = self.max_number_of_paths_list[
                    random.randrange(0, len(self.max_number_of_paths_list))]

            iteration_counter += 1
            if time.time() - start_time > 1800:  # If more than 30 mins have passed, save and break
                output_format_solution = self.convert_to_pace_format(best)
                self.save_solution(
                    instance_name, output_format_solution, best.fitness)
                break

            # Only terminate the loop if it's a forced termination and 30 mins have passed
            if killer.exit_now and time.time() - start_time > 1800:
                output_format_solution = self.convert_to_pace_format(best)
                self.save_solution(
                    instance_name, output_format_solution, best.fitness)
                break

        return best

    def perturb(self, s, iteration_counter, iteration_no_improvement_counter):
        current_solution = copy(s)
        additional_perturbations = int(log(
            int(1 + iteration_no_improvement_counter / self.number_of_iterations_with_no_improvement), 2))
        for i in range(self.minimal_perturb_intensity + additional_perturbations):
            selected_nodes, node_type = self.select_nodes(
                current_solution, iteration_counter)
            new_solution = self.move_node(
                current_solution, selected_nodes, node_type)
            additional_deprecation = additional_perturbations / 100
            if new_solution.fitness * (
                    self.perturbed_solution_deprecation_percentage - additional_deprecation) < current_solution.fitness:
                current_solution = copy(new_solution)
        return current_solution

    def get_key(self, new_solution):
        key = self.solution_node_sequence(
            new_solution.representation, new_solution.root)
        return key

    def solution_node_sequence(self, representation, parent):
        child_list = representation[parent]
        if len(child_list) == 0:
            result = ''
        elif len(child_list) == 1:
            result = str(
                child_list[0]) + self.solution_node_sequence(representation, child_list[0])
        else:
            for child in child_list:
                result = str(child) + \
                    self.solution_node_sequence(representation, child)
        return result

    def select_nodes(self, s, iteration_counter):
        tabu_status = True
        while tabu_status:
            random_number = random.randrange(0, 101)
            if random_number <= node_type_selection_probability['subtree']:
                selected_nodes = self.get_sub_tree_nodes(
                    s.representation, s.fitness, s.root)
                node_type = 'subtree'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal']:
                selected_nodes = [self.get_internal_node(
                    s.representation, s.root)]
                node_type = 'internal'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf']:
                selected_nodes = [self.get_leaf_node(s.representation)]
                node_type = 'leaf'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root']:
                selected_nodes = [s.root]
                node_type = 'root'
                tabu_status = False
                break
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root'] + \
                    node_type_selection_probability['top']:
                selected_nodes = self.get_top_nodes(s)
                node_type = 'top'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root'] + \
                    node_type_selection_probability['top'] + \
                    node_type_selection_probability['level']:
                selected_nodes = self.get_longer_level_nodes(s)
                node_type = 'level'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root'] + \
                    node_type_selection_probability['top'] + \
                    node_type_selection_probability['level'] + \
                    node_type_selection_probability['path']:
                selected_nodes = self.get_longer_path_nodes(s)
                node_type = 'path'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root'] + \
                    node_type_selection_probability['top'] + \
                    node_type_selection_probability['level'] + \
                    node_type_selection_probability['path'] + \
                    node_type_selection_probability['leafs']:
                selected_nodes = self.get_leaf_nodes_with_non_related_parent(
                    s.representation, s.root)
                node_type = 'leafs'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root'] + \
                    node_type_selection_probability['top'] + \
                    node_type_selection_probability['level'] + \
                    node_type_selection_probability['path'] + \
                    node_type_selection_probability['leafs'] + \
                    node_type_selection_probability['partial_path']:
                selected_nodes = self.get_partial_path_nodes(s)
                node_type = 'partial_path'
            elif random_number <= node_type_selection_probability['subtree'] + \
                    node_type_selection_probability['internal'] + \
                    node_type_selection_probability['leaf'] + \
                    node_type_selection_probability['root'] + \
                    node_type_selection_probability['top'] + \
                    node_type_selection_probability['level'] + \
                    node_type_selection_probability['path'] + \
                    node_type_selection_probability['leafs'] + \
                    node_type_selection_probability['partial_path'] + \
                    node_type_selection_probability['partial_path_bottom']:
                selected_nodes = self.get_partial_path_from_bottom_nodes(
                    s.representation, s.fitness, s.root)
                node_type = 'partial_path_bottom'
            else:
                selected_nodes = self.get_bottom_nodes(s)
                node_type = 'bottom'
            for n in selected_nodes:
                tabu_feature = str(n) + '-' + str(s.root)
                tabu_status = self.is_tabu(tabu_feature, iteration_counter)
                if tabu_status:
                    break
        return selected_nodes, node_type

    @staticmethod
    def get_top_nodes(s):
        result = list()
        q_parents = Queue()
        q_parents.put([s.root])
        top_depth = random.randrange(
            2, int(s.fitness * top_max_limit_probability) + 1)
        for d in range(top_depth):
            parents = q_parents.get()
            children = list()
            for parent in parents:
                result.append(parent)
                for c in s.representation[parent]:
                    children.append(c)
            q_parents.put(children)
        return result

    def get_longer_level_nodes(self, s):
        result = self.get_level_nodes(s)
        max_level = len(result)
        for i in range(random.randrange(1, self.max_number_of_paths)):
            node_to_move_list = self.get_level_nodes(s)
            if len(node_to_move_list) > max_level:
                result = node_to_move_list
                max_level = len(node_to_move_list)
        return result

    @staticmethod
    def get_level_nodes(s):
        q_parents = Queue()
        q_parents.put([s.root])
        depth_level = random.randrange(2, s.fitness + 1)
        for d in range(depth_level):
            parents = q_parents.get()
            children = list()
            for parent in parents:
                for c in s.representation[parent]:
                    children.append(c)
            q_parents.put(children)
        return parents

    @staticmethod
    def get_path_nodes(s):
        result = list()
        parent = s.root
        leaf_level_reached = False
        while not leaf_level_reached:
            result.append(parent)
            child_list = s.representation[parent]
            if len(child_list) > 0:
                child = child_list[random.randrange(0, len(child_list))]
                parent = child
            else:
                leaf_level_reached = True
        return result

    def get_longer_path_nodes(self, s):
        result = self.get_path_nodes(s)
        max_path = len(result)
        for i in range(random.randrange(1, self.max_number_of_paths)):
            node_to_move_list = self.get_path_nodes(s)
            if len(node_to_move_list) > max_path:
                result = node_to_move_list
                max_path = len(node_to_move_list)
        return result

    def get_partial_path_nodes(self, s):
        all_path_nodes_list = self.get_path_nodes(s)
        max_path = len(all_path_nodes_list)
        for i in range(random.randrange(1, self.max_number_of_paths)):
            node_to_move_list = self.get_path_nodes(s)
            if len(node_to_move_list) > max_path:
                all_path_nodes_list = node_to_move_list
                max_path = len(node_to_move_list)
        all_path_nodes = len(all_path_nodes_list)
        partial_path_start_position = all_path_nodes - random.randrange(1, max(2, int(
            all_path_nodes * self.max_partial_path_length_percentage)))
        result = list()
        # print("path length: ", (all_path_nodes - partial_path_start_position))
        for i in range(partial_path_start_position - 1, all_path_nodes):
            result.append(all_path_nodes_list[i])
        return result

    def get_bottom_nodes(self, s):
        top_nodes = list()
        q_parents = Queue()
        q_parents.put([s.root])
        bottom_depth = random.randrange(
            1, max(2, int(s.fitness * bottom_depth_max_limit_probability) + 1))
        for d in range(s.fitness - bottom_depth):
            parents = q_parents.get()
            children = list()
            for parent in parents:
                top_nodes.append(parent)
                for c in s.representation[parent]:
                    children.append(c)
            q_parents.put(children)
        result = list(set(self.number_of_edges_list) - set(top_nodes))
        return result

    @staticmethod
    def get_leaf_node(representation):
        random_start_index = random.randrange(0, len(representation))
        random_walk = random.randrange(
            0, int(random_walk_limit * len(representation)))
        rw_counter = 0
        node = random_start_index
        while node < len(representation):
            if len(representation[node]) == 0:
                if rw_counter == random_walk:
                    return node
                rw_counter += 1
            if node != len(representation) - 1:
                node += 1
            else:
                node = 0

    @staticmethod
    def get_leaf_nodes(representation):
        result = list()
        for node in range(len(representation)):
            child_list = representation[node]
            if len(child_list) == 0:
                result.append(node)
        return result

    def get_leaf_nodes_with_non_related_parent(self, representation, root):
        result = list()
        for node in range(len(representation)):
            child_list = representation[node]
            if len(child_list) == 0:
                if node in representation[root]:
                    parent = root
                else:
                    parent = self.find_non_root_parent_node(
                        representation, node)
                if node not in self.adjacency_list[parent]:
                    result.append(node)
        return result

    def get_internal_node(self, representation, root):
        random_start_index = random.randrange(0, len(representation))
        random_walk = random.randrange(
            0, int(random_walk_limit * len(representation)))
        rw_counter = 0
        node = random_start_index
        while node < len(representation):
            if len(representation[node]) != 0 and node != root:
                if node in representation[root]:
                    parent = root
                else:
                    parent = self.find_non_root_parent_node(
                        representation, node)
                if node not in self.adjacency_list[parent]:
                    result = node
                    break
                if rw_counter == random_walk:
                    result = node
                    break
                rw_counter += 1
            if node != len(representation) - 1:
                node += 1
            else:
                node = 0
        return result

    def get_sub_tree_nodes(self, representation, fitness, root):
        random_start_index = random.randrange(0, len(representation))
        random_walk = random.randrange(
            1, max(2, int(sub_tree_size_probability * fitness)))
        node = random_start_index
        while node < len(representation):
            if len(representation[node]) == 0:
                leaf_node = node
                break
            if node != len(representation) - 1:
                node += 1
            else:
                node = 0
        current_leaf_node = leaf_node
        for i in range(random_walk):
            parent = self.find_non_root_parent_node(
                representation, current_leaf_node)
            if parent == root:
                break  # root node is not included
            current_leaf_node = parent
        result = [current_leaf_node]
        result.extend(self.get_node_successors(
            representation, current_leaf_node))
        return result

    def get_partial_path_from_bottom_nodes(self, representation, fitness, root):
        random_start_index = random.randrange(0, len(representation))
        random_walk = random.randrange(
            1, max(2, int(self.max_partial_path_length_percentage * fitness)))
        node = random_start_index
        result = list()
        while node < len(representation):
            if len(representation[node]) == 0:
                leaf_node = node
                break
            if node != len(representation) - 1:
                node += 1
            else:
                node = 0
        current_leaf_node = leaf_node
        result.append(current_leaf_node)
        for i in range(random_walk):
            parent = self.find_non_root_parent_node(
                representation, current_leaf_node)
            if parent == root:
                break  # root node is not included
            if current_leaf_node not in self.adjacency_list[parent]:
                break
            current_leaf_node = parent
            result.append(current_leaf_node)
        return result

    def get_node_successors(self, representation, parent):
        child_list = representation[parent]
        if len(child_list) == 0:
            return list()
        elif len(child_list) == 1:
            child = child_list[0]
            result = list([child])
            result.extend(self.get_node_successors(
                representation, child_list[0]))
        else:
            result = list()
            for child in child_list:
                result.append(child)
                result.extend(self.get_node_successors(representation, child))
        return result

    def move_node(self, s, nodes_to_move, node_type):
        representation = deepcopy(s.representation)
        if node_type == 'root':
            node_to_move = nodes_to_move[0]
            current_root_child_list = s.representation[s.root]
            representation[node_to_move] = list()
            if len(current_root_child_list) == 1:
                new_root = current_root_child_list[0]
            else:
                new_root = current_root_child_list[random.randrange(
                    0, len(current_root_child_list))]
                for n in current_root_child_list:
                    if n != new_root:
                        representation[new_root].append(n)
            self.place_node(representation, new_root, new_root, node_to_move)
        elif node_type == 'top':
            root_pretenders = list()
            s1 = set(nodes_to_move)
            for i in range(len(nodes_to_move) - 1, -1, -1):
                current_node = nodes_to_move[i]
                current_node_child_list = s.representation[current_node]
                s2 = set(current_node_child_list)
                if len(list(s1.intersection(s2))) == 0:
                    root_pretenders.extend(current_node_child_list)
                else:
                    break
            for n in nodes_to_move:
                representation[n] = list()
            if len(root_pretenders) == 1:
                new_root = root_pretenders[0]
            else:
                new_root = root_pretenders[random.randrange(
                    0, len(root_pretenders))]
                for n in root_pretenders:
                    if n != new_root:
                        representation[new_root].append(n)
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        elif node_type == 'path':
            new_root_assigned = False
            parent_to_link = -1
            if len(nodes_to_move) == len(representation):
                return self.get_initial_solution()
            else:
                for n in range(len(nodes_to_move) - 1):
                    current_parent = nodes_to_move[n]
                    current_child = nodes_to_move[n + 1]
                    child_list = list(representation[current_parent])
                    representation[current_parent] = list()
                    child_list.remove(current_child)
                    if len(child_list) > 0:
                        new_parent = child_list[random.randrange(
                            0, len(child_list))]
                        child_list.remove(new_parent)
                        representation[new_parent].extend(child_list)
                        if not new_root_assigned:
                            new_root = new_parent
                            new_root_assigned = True
                        else:
                            representation[parent_to_link].append(new_parent)
                        parent_to_link = new_parent
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        elif node_type == 'partial_path':
            if len(nodes_to_move) < 2:
                print("new initial solution")
                return self.get_initial_solution()
            new_root = s.root
            parent_to_link = nodes_to_move[0]
            representation[parent_to_link].remove(nodes_to_move[1])
            # First node does not get removed - it serves as parent
            for n in range(1, len(nodes_to_move) - 1):
                current_parent = nodes_to_move[n]
                current_child = nodes_to_move[n + 1]
                child_list = list(representation[current_parent])
                representation[current_parent] = list()
                child_list.remove(current_child)
                if len(child_list) > 0:
                    new_parent = child_list[random.randrange(
                        0, len(child_list))]
                    child_list.remove(new_parent)
                    representation[new_parent].extend(child_list)
                    representation[parent_to_link].append(new_parent)
                    parent_to_link = new_parent
            nodes_to_move.pop(0)  # Remove first node
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        elif node_type == 'partial_path_bottom':
            new_root = s.root
            nodes_to_move.reverse()
            parent_to_link = self.find_non_root_parent_node(
                s.representation, nodes_to_move[0])
            if parent_to_link == -1:
                parent_to_link = new_root
            representation[parent_to_link].remove(nodes_to_move[0])
            for n in range(0, len(nodes_to_move) - 1):
                current_parent = nodes_to_move[n]
                current_child = nodes_to_move[n + 1]
                child_list = list(representation[current_parent])
                representation[current_parent] = list()
                child_list.remove(current_child)
                if len(child_list) > 0:
                    new_parent = child_list[random.randrange(
                        0, len(child_list))]
                    child_list.remove(new_parent)
                    representation[new_parent].extend(child_list)
                    representation[parent_to_link].append(new_parent)
                    parent_to_link = new_parent
            if len(nodes_to_move) > 1:
                nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        elif node_type == 'level':
            new_root = s.root
            for node in nodes_to_move:
                current_node_parent = self.find_non_root_parent_node(
                    s.representation, node)
                representation[current_node_parent].remove(node)
                representation[current_node_parent].extend(
                    representation[node])
                representation[node] = list()
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        elif node_type == 'bottom':
            new_root = s.root
            for node in nodes_to_move:
                current_node_parent = self.find_non_root_parent_node(
                    s.representation, node)
                if (current_node_parent not in nodes_to_move) and (node in representation[current_node_parent]):
                    representation[current_node_parent].remove(node)
            for node in nodes_to_move:
                representation[node] = list()
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        elif node_type == 'leaf':
            node_to_move = nodes_to_move[0]
            new_root = s.root
            current_parent = self.find_non_root_parent_node(
                representation, node_to_move)
            representation[current_parent].remove(node_to_move)
            self.place_node(representation, new_root, new_root, node_to_move)
        elif node_type == 'leafs':
            new_root = s.root
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node_to_move in nodes_to_move:
                current_parent = self.find_non_root_parent_node(
                    representation, node_to_move)
                representation[current_parent].remove(node_to_move)
                self.place_node(representation, new_root,
                                new_root, node_to_move)
        elif node_type == 'internal':
            node_to_move = nodes_to_move[0]
            new_root = s.root
            node_child_list = s.representation[node_to_move]
            root_child_list = s.representation[s.root]
            if node_to_move in root_child_list:
                parent = s.root
            else:
                parent = self.find_non_root_parent_node(
                    representation, node_to_move)
            representation[parent].remove(node_to_move)
            representation[parent].extend(node_child_list)
            representation[node_to_move] = list()
            self.place_node(representation, new_root, new_root, node_to_move)
        else:  # subtree
            new_root = s.root
            parent_node = nodes_to_move[0]
            parent_of_parent = self.find_non_root_parent_node(
                representation, parent_node)
            representation[parent_of_parent].remove(parent_node)
            for node in nodes_to_move:
                representation[node] = list()
            nodes_to_move = self.get_ordered_node_list(nodes_to_move)
            for node in nodes_to_move:
                self.place_node(representation, new_root, new_root, node)
        fitness = self.get_fitness(representation, new_root)
        result = Solution(new_root, representation, fitness)
        return result

    def place_node(self, representation, parent, current_node_to_link, node):
        is_internal_node = False
        node_to_link, is_internal_node = self.find_node_to_link(representation, parent, current_node_to_link, node,
                                                                is_internal_node)
        if is_internal_node:
            child_list = representation[node_to_link]
            representation[node_to_link] = list()
            representation[node_to_link].append(node)
            representation[node] = list(child_list)
        else:
            representation[node_to_link].append(node)

    def get_simple_initial_solution(self):
        representation = list()
        for i in range(self.n_nodes):
            lst = list()
            representation.append(lst)
        root = self.number_of_edges_list[0]
        first_child = self.number_of_edges_list[1]
        representation[root].append(first_child)
        for node in range(1, self.n_nodes - 1):
            parent = self.number_of_edges_list[node]
            child = self.number_of_edges_list[node + 1]
            representation[parent].append(child)
        fitness = self.get_fitness(representation, root)
        initial_solution = Solution(root, representation, fitness)
        selected_nodes = self.get_top_nodes(initial_solution)
        node_type = 'top'
        result = self.move_node(initial_solution, selected_nodes, node_type)
        return result

    def get_initial_solution(self):
        representation = list()
        for i in range(self.n_nodes):
            lst = list()
            representation.append(lst)
        root = self.number_of_edges_list[0]
        first_child = self.number_of_edges_list[1]
        representation[root].append(first_child)
        for n in range(2, self.n_nodes, 1):
            node = self.number_of_edges_list[n]
            is_internal_node = False
            node_to_link, is_internal_node = self.find_node_to_link(
                representation, root, root, node, is_internal_node)
            if is_internal_node:
                child_list = representation[node_to_link]
                representation[node_to_link] = list()
                representation[node_to_link].append(node)
                representation[node] = list(child_list)
            else:
                representation[node_to_link].append(node)
        fitness = self.get_fitness(representation, root)
        result = Solution(root, representation, fitness)
        # if fitness < 11:
        #     print('test')
        return result

    def find_node_to_link(self, representation, parent, current_node_to_link, node, is_internal_node):
        node_to_link = current_node_to_link
        child_list = representation[parent]
        if len(child_list) == 0:
            return node_to_link, is_internal_node
        elif len(child_list) == 1:
            node_to_link_candidate = child_list[0]
            if node in self.adjacency_list[node_to_link_candidate]:
                node_to_link = node_to_link_candidate
            node_to_link, is_internal_node = self.find_node_to_link(representation, node_to_link_candidate,
                                                                    node_to_link, node, is_internal_node)
        else:
            num_paths = 0
            for child in child_list:
                previous_node_to_link = node_to_link
                if node in self.adjacency_list[child]:
                    node_to_link = child
                node_to_link, is_internal_node = self.find_node_to_link(representation, child, node_to_link, node,
                                                                        is_internal_node)
                if previous_node_to_link != node_to_link:
                    num_paths += 1
                    if num_paths == 2:
                        node_to_link = parent
                        is_internal_node = True
                        break
        return node_to_link, is_internal_node

    def get_fitness(self, representation, root):
        result = 1 + self.calculate_fitness(representation, root)
        return result

    def calculate_fitness(self, representation, parent):
        child_list = representation[parent]
        if len(child_list) == 0:
            fitness = 0
        elif len(child_list) == 1:
            fitness = 1 + self.calculate_fitness(representation, child_list[0])
        else:
            max_fitness = -1
            for child in child_list:
                current_fitness = 1 + \
                    self.calculate_fitness(representation, child)
                if current_fitness > max_fitness:
                    max_fitness = current_fitness
            fitness = max_fitness
        return fitness

    @staticmethod
    def find_non_root_parent_node(representation, node):
        for c in range(len(representation)):
            child_list = representation[c]
            if node in child_list:
                return c
        return -1

    def is_tabu(self, key, iteration):
        if key not in self.tabu_list.keys():
            return False
        if iteration - self.tabu_list[key] <= self.tabu_list_length_probability * self.n_nodes:
            return True
        else:
            return False

    def create_number_of_edges_list(self):
        node_list_with_n_edges = list()
        for i in range(len(self.adjacency_list)):
            node_list_with_n_edges.append([i, len(self.adjacency_list[i])])
        node_list_with_n_edges.sort(key=itemgetter(1),
                                    reverse=self.insert_nodes_in_initial_solution_descending_order)
        current_max_n_edges = node_list_with_n_edges[0][1]
        result = list()
        current_list = list()
        for m in range(len(node_list_with_n_edges)):
            if node_list_with_n_edges[m][1] == current_max_n_edges:
                current_list.append(node_list_with_n_edges[m][0])
            else:
                random.shuffle(current_list)
                result.extend(current_list)
                current_list = list()
                current_list.append(node_list_with_n_edges[m][0])
                current_max_n_edges = node_list_with_n_edges[m][1]
        result.extend(current_list)
        return result

    def get_ordered_node_list(self, node_list):
        if self.insert_nodes_in_random_order:
            random.shuffle(node_list)
            return node_list
        node_list_with_n_edges = list()
        for node in node_list:
            node_list_with_n_edges.append(
                [node, len(self.adjacency_list[node])])
        node_list_with_n_edges.sort(key=itemgetter(
            1), reverse=self.insert_nodes_in_descending_order)
        current_max_n_edges = node_list_with_n_edges[0][1]
        result = list()
        current_list = list()
        for m in range(len(node_list_with_n_edges)):
            if node_list_with_n_edges[m][1] == current_max_n_edges:
                current_list.append(node_list_with_n_edges[m][0])
            else:
                random.shuffle(current_list)
                result.extend(current_list)
                current_list = list()
                current_list.append(node_list_with_n_edges[m][0])
                current_max_n_edges = node_list_with_n_edges[m][1]
        result.extend(current_list)
        return result

    def get_fitness(self, representation, root):
        result = 1 + self.calculate_fitness(representation, root)
        return result

    def calculate_fitness(self, representation, parent):
        child_list = representation[parent]
        if len(child_list) == 0:
            fitness = 0
        elif len(child_list) == 1:
            fitness = 1 + self.calculate_fitness(representation, child_list[0])
        else:
            max_fitness = -1
            for child in child_list:
                current_fitness = 1 + \
                    self.calculate_fitness(representation, child)
                if current_fitness > max_fitness:
                    max_fitness = current_fitness
            fitness = max_fitness
        return fitness

    def get_adjacency_list(self, file_name):
        adjacency_list = {}
        # edge_graph = nx.Graph()
        file = open('instances/' + file_name, 'r')
        first_line = file.readline().split(' ')
        total_points = int(first_line[2])
        self.n_list.append(int(first_line[2]))
        n_nodes = int(first_line[2])
        self.e_list.append(int(first_line[3]))
        n_edges = int(first_line[3])
        self.fill_adjacency_list(total_points, adjacency_list)
        file_rows = filter(None, file.read().split('\n'))
        for row in file_rows:
            element = row.split(' ')
            node1 = int(element[0]) - 1  # convert node1 to a zero based index
            node2 = int(element[1]) - 1  # convert node2 to a zero based index
            # edge_graph.add_edge(node1, node2)
            if node1 in adjacency_list:
                adjacency_list[node1].append(node2)
            if node2 in adjacency_list:
                adjacency_list[node2].append(node1)
        return adjacency_list, n_nodes, n_edges

    def fill_adjacency_list(self, total_points, adjacency_list):
        for i in range(total_points):
            adjacency_list[i] = []

    def convert_to_pace_format(self, s):
        result = [-1] * len(s.representation)
        result[s.root] = 0  # revert to one based index
        for i in range(len(s.representation)):
            node_list = s.representation[i]
            if len(node_list) > 0:
                for node in node_list:
                    result[node] = i + 1  # revert to one based index
        return result

    def save_solution(self, _output_file, formatted_solution, fitness):
        file_name = _output_file[0:9]
        try:
            file = open('solutions/' + file_name + '.tree', "w+")
            file.write(str(fitness) + "\n")
            for i in formatted_solution:
                file.write(str(i) + "\n")
            file.close()
        except OSError as e:
            print(
                "Make sure that you have created a folder named 'solutions' in the same folder where you have saved the solver ")
            print("Error message: " + e.strerror)
            exit()

    @staticmethod
    def count_duplicates_test(representation):
        duplicate_list = list()
        for c in range(len(representation)):
            child_list = representation[c]
            for node in child_list:
                if node in duplicate_list:
                    return True
                else:
                    duplicate_list.append(node)
        return False


if __name__ == '__main__':
    sys.setrecursionlimit(recursion_limit)
    if len(sys.argv) == 1:
        print("The input instance is not specified!")
    elif len(sys.argv) > 2:
        print("Too many arguments")
    else:
        try:
            instance_argument = sys.argv[1]
            instance_argument = instance_argument.lower()
            instance_argument = instance_argument[2:]
            if instance_argument[0:5] == 'exact':
                instance_name = instance_argument
                ils_alg = IteratedLocalSearch(instance_name)
                s = ils_alg.ils_algorithm()
                print("The tree depth for instance '" + instance_name + "' is '{0}' ".format(s.fitness),
                      "and the the corresponding solution is saved in the folder named 'solutions'.")
                formatted_solution = ils_alg.convert_to_pace_format(s)
                ils_alg.save_solution(
                    instance_name, formatted_solution, s.fitness)
            else:
                if instance_argument == 'private':
                    start_instance_index = 1
                    end_instance_index = 200
                elif instance_argument == 'public':
                    start_instance_index = 1
                    end_instance_index = 199
                for i in range(start_instance_index, end_instance_index + 1, 2):
                    instance_name = instance_type + "_" + "{0:03}".format(i)
                    ils_alg = IteratedLocalSearch(instance_name + '.gr')
                    s = ils_alg.ils_algorithm()
                    print("The tree depth for instance '" + instance_name + ".gr' is '{0}' ".format(s.fitness),
                          "and the the corresponding solution is saved in the folder named 'solutions'.")
                    formatted_solution = ils_alg.convert_to_pace_format(s)
                    ils_alg.save_solution(
                        instance_name, formatted_solution, s.fitness)
        except OSError as e:
            print("Instance '" + instance_name + "' not found!")
            print("Make sure that all private/public instances are placed in a folder named 'instances',",
                  "which should be located in the same folder as the solver.")
            print("Error message: " + e.strerror)
