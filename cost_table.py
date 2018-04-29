#!/usr/bin/env python

############################################
#               Ben Arbib                  #
#                  P2                      #
#          JRIP34 - cost_table             #
#    object that handles the cost table    #
#               COMS 4119                  #
############################################


class cost_table:
    def __init__(self, list_of_neighbors):
        # initialize the table
        self.table = {}
        self.table["SEQ"] = -1  # not sure if neede?
        self.table["Data"] = {}
        self.table["Data"]["Type"] = "JRIP"
        self.table["Data"]["RIPTable"] = []
        self.neighbors = {}

        for n in list_of_neighbors:
            ip, port, cost = n.split(":")
            nid = ip+":"+port

            new_neighbor = {}
            neighbors[nid] = cost
            new_neighbor["Dest"] = nid
            new_neighbor["Next"] = nid 
            new_neighbor["Cost"] = cost
            self.table["Data"]["RIPTable"].append(copy.deepcopy(new_neighbor))

    def update_table(self, other_table, from_ip):
        cost_list = other_table["Data"]["RIPTable"]
        my_list = self.table["Data"]["RIPTable"]
        
        for n in cost_list:
            found = False
            for m in my_list:
                if m["Dest"] == n["Dest"]:
                    if n["Cost"] < m["Cost"]+neighbors[from_ip]:
                        m["Cost"] = neighbors[from_ip] + n["Cost"]
                        m["Next"] = from_ip
                    found = True
                    break
            if not Found:
                new_dest = {}
                new_dest["Dest"] = n["Dest"]
                new_dest["Next"] = n["Next"]
                new_dest["Cost"] = n["Cost"] + neighbors[from_ip]
                my_list.append(new_dest)

    def get_all_neigbors(self):
        return neighbors

    def get_table(self):
        return self.table

