import copy
from collections import namedtuple
import re
import requests
from bs4 import BeautifulSoup
import json

url = 'https://en.wikipedia.org/wiki/2020_coronavirus_pandemic_in_Romania'

Case = namedtuple('Case', "id date age sex origin_of_infection detection_location source_of_infection status notes")


def get_cases() -> [Case]:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.findAll('table', {"class": "wikitable"})
    raw_cases = tables[0]
    headers = raw_cases.findAll('th')
    rows = raw_cases.findAll('tr')
    header_idx = {}  # type: dict[str, int]
    for idx, h in enumerate(headers):
        header_idx[h.get_text(strip=True)] = idx
    cases_data = []  # type: [{}]
    extra_idxs = {}  # type: {int, (int, str)}
    for row_idx, r in enumerate(rows[1:]):
        tds = r.findAll('td')
        data = [(int(d.get("rowspan", '1')), d.get_text(strip=True)) for d in tds]  # type: [(int, str)]
        for extraIdx, (numExtra, val) in copy.deepcopy(extra_idxs).items():
            data.insert(extraIdx, (numExtra - 1, val))
            if numExtra - 1 == 0:
                extra_idxs[extraIdx] = (numExtra - 1, val)
            else:
                del extra_idxs[extraIdx]

        for idx, (rw, d) in enumerate(data):
            if rw > 1:
                extra_idxs[idx] = (rw, d)

        case_row = Case(row_idx + 1,
                        data[header_idx['Date'] - 1][1],
                        data[header_idx['Age'] - 1][1],
                        data[header_idx['Sex'] - 1][1],
                        data[header_idx['Origin of infection'] - 1][1],
                        data[header_idx['Detection location'] - 1][1],
                        data[header_idx['Source of infection'] - 1][1],
                        data[header_idx['Status'] - 1][1],
                        data[header_idx['Notes'] - 1][1])
        cases_data.append(case_row)
    return cases_data


def find_links(cs: [Case]) -> dict:
    links = {}
    for c in cs:
        possible_link = re.findall(r"#\d+", c.notes)
        links[c.id] = [int(p.lstrip("#")) for p in possible_link]
        # if c.origin_of_infection != "N/A":
        #     links[c.id].append(0)
    return links


if __name__ == '__main__':
    cases = get_cases()
    # Add base case
    # cases.append(Case(0, '', '', '', 'Italy', 'Italy', 'Italy', 'Is Italy', "Hospitalized"))

    cases_dict = {c.id: c for c in cases}
    links = find_links(cases)
    cases_links = [{"source": case_source, "target": case_dest, "value": 1} for (case_dest, source_list) in links.items() for case_source in source_list]
    cases_json = ([dict(c._asdict()) for c in cases])
    cases_links_json = cases_links

    with open('cases.json', 'w') as outfile:
        json.dump(cases_json, outfile)

    with open('cases_links.json', 'w') as outfile:
        json.dump(cases_links_json, outfile)
