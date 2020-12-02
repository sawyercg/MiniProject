"""
This is where the implementation of the plugin code goes.
The PetriNetCodeGenerator-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
import json
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('PetriNetCodeGenerator')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class PetriNetCodeGenerator(PluginBase):
    def main(self):
        logger.info("TEST")
        core = self.core
        root_node = self.root_node
        active_node = self.active_node
        META = self.META

        name = core.get_attribute(active_node, 'name')

        logger.info('ActiveNode at "{0}" has name {1}'.format(core.get_path(active_node), name))

        core.set_attribute(active_node, 'name', 'newName')

        commit_info = self.util.save(root_node, self.commit_hash, 'master', 'Python plugin updated the model')
        logger.info('committed :{0}'.format(commit_info))
        nodes = {}
        self.places = []
        self.markings= dict()
        self.inPlaces= []
        self.outPlaces = []
        self.transitions = []
        self.pathToNode = dict()
        for node in core.load_sub_tree(active_node):
            self.pathToNode[core.get_path(node)] = node
            if core.is_type_of(node, META["Place"]):
                self.markings[core.get_path(node)] = core.get_attribute(node, "tokens")
                self.places.append(node)
            elif core.is_type_of(node, META["Inplace"]):
                self.inPlaces.append(node)
            elif core.is_type_of(node, META["Outplace"]):
                self.outPlaces.append(node)
            elif core.is_type_of(node, META["Transition"]):
                self.transitions.append(node)
        isState = self.is_state_machine()
        isMarked = self.is_marked_graph()
        isFree = self.is_free_choice()
        isWorkFlow = self.is_workflow()


        msg = {
           "State Machine": isState,
           "Marked Graph": isMarked,
           "Free Choice": isFree,
           "Work Flow": isWorkFlow,
        }
        msg = json.dumps(msg)
        logger.info(msg)
        self.create_message(active_node, msg)

        logger.info("State Machine: " + str(isState))
        logger.info("Marked Garph: " + str(isMarked))
        logger.info("Free Choice: " + str(isFree))
        logger.info("Work Flow Diagram: " + str(isWorkFlow))


    def is_state_machine(self):
        for t in self.transitions:
            ins = 0
            outs = 0
            for i in self.inPlaces:
                if self.core.get_pointer_path(i, "src") == self.core.get_path(t):
                    ins += 1
            if ins != 1:
                return False
            for i in self.outPlaces:
                if self.core.get_pointer_path(i, "dst") == self.core.get_path(t):
                    outs += 1
            if outs != 1:
                return False
        return True

    def is_marked_graph(self):
        for p in self.places:
            ins = 0
            outs = 0
            for i in self.inPlaces:
                if self.core.get_pointer_path(i, "dst") == self.core.get_path(p):
                    outs += 1
            if outs != 1:
                return False
            for i in self.outPlaces:
                if self.core.get_pointer_path(i, "src") == self.core.get_path(p):
                    ins += 1
            return ins == 1

    def is_free_choice(self):
        pairs = dict()
        for i in self.inPlaces:
            place = self.core.get_pointer_path(i, "dst")
            trans = self.core.get_pointer_path(i, "src")
            inPlace = pairs.get(place, trans)

            if inPlace != trans:
                return False
            else:
                pairs[place] = trans
        return True

    def is_workflow(self):
        sources = self.places.copy()
        sinks = self.places.copy()

        for i in self.outPlaces:
            src = self.pathToNode[self.core.get_pointer_path(i, "src")]
            if src in sources:
                sources.remove(src)
        if len(sources) != 1:
            return False
        for i in self.inPlaces:
            dst = self.pathToNode[self.core.get_pointer_path(i, "dst")]
            if dst in sinks:
                sinks.remove(dst)
        if len(sinks) != 1:
            return False

        ## all places and transitions are on the path if there are no sink/source transitions

        sources = self.transitions.copy()
        sinks = self.transitions.copy()

        for i in self.outPlaces:
            dst = self.pathToNode[self.core.get_pointer_path(i, "dst")]
            if dst in sinks:
                sinks.remove(dst)
        if len(sources) != 0:
            return False
        for i in self.inPlaces:
            src = self.pathToNode[self.core.get_pointer_path(i, "src")]
            if src in sources:
                sources.remove(src)
        if len(sinks) != 0:
            return False
        return True