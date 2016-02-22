#!/usr/bin/env python3

from starwatts import StarWatts


def main():
    s = StarWatts('conf.yml')
    c = s.get_connection()
    sg_dc = dict()
    for sg in c.get_all_security_groups():
        for i in sg.instances():
            if i.id in sg_dc:
                sg_dc[i.id].append(sg.name)
            else:
                sg_dc[i.id] = [sg.name, ]

    for inst in c.get_only_instances():
        print("{name:20}{id}\t{sg}".format(
            name=inst.tags.get('name', 'No Name'),
            id=inst.id,
            sg=", ".join(sg_dc.get(inst.id, [])),
        ))

if __name__ == '__main__':
    main()
