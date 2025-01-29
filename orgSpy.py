import json
import requests
import shutil
import sqlite3
import textwrap

class orgSpy():

    def __init__(self, **kwargs):

        self.headers = {'user-agent':'Screaming Frog SEO Spider/6.2'}
        self.__dict__.update(kwargs)


    def recon(self):

        conn = sqlite3.connect("orgSpy.db")
        cursor = conn.cursor()
        cursor.execute("SELECT slug FROM slugs WHERE domain = ?", (self.domain,))
        results = cursor.fetchall()

        if results:
            slug, = results[0]
            json_data = {
                'variables': {
                    'slug': slug,
                },
                'query': "query company($slug: String!){ company(slug:$slug){ name extensions id social{ websiteUrl linkedInUrl twitterUrl facebookUrl } logoImage{endpoint uri extensions} location{street city state postalCode country} description stats{employeeRange} industries{title} nodes{...PositionNode}}} fragment PositionNode on OrgChartStructureNode{node{... on Position {position{id slug fullName role social{linkedInUrl} description location{state} profileImage{endpoint uri extensions}}}}}"
            }
            response = requests.post('https://prod-graphql-api.theorg.com/graphql', headers=self.headers, json=json_data)
            results = response.json().get("data").get("company")
            
            result = {
                "company_name":results.get("name"),
                "domains":results.get("extensions"),
                "socials":[social for social in list(results.get("social").values()) if social is not None],
                "logo":results.get("logoImage").get("endpoint") + "/" + results.get("logoImage").get("uri") + "." + results.get("logoImage").get("extensions")[0],
                "description":results.get("description"),
                "people":[{"name":node.get("node").get("position").get("fullName"), "role":node.get("node").get("position").get("role"), "socials":node.get("node").get("position").get("social"), "description":node.get("node").get("position").get("description")} for node in results.get("nodes") if node.get("node") != {} ]
            }

            return result
        
        else:
            return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description = "Gather OSINT about a company and employees from TheOrg.com")
    parser.add_argument("domain", help="The primary domain of the org being investigated")
    parser.add_argument("--json",required=False, action="store_true", help="Return results as JSON")
    parser.add_argument("--descriptions",required=False, action="store_true", help="Include employee descriptions in results")
    
    args = parser.parse_args()

    try:
        org_spy =  orgSpy(**vars(args))
        results = org_spy.recon()

        if org_spy.json:
            if results:
                print(json.dumps(results))
            else:
                print("[]")

        else:
            if results:
                if results.get("company_name"):
                    print(f"\n{results.get('company_name')}")
                if results.get("description"):
                    print(f"\t{results.get('description')}")

                if results.get("domains"):
                    print(f"\nDOMAINS ({len(results.get('domains'))}):")
                    for domain in results.get("domains"):
                        print(f"\t{domain}")

                if results.get("socials"):
                    print(f"\nSOCIALS ({len(results.get('socials'))}):")
                    for social in results.get("socials"):
                        print(f"\t{social}")

                if results.get("people"):
                    print(f"\nPEOPLE ({len(results.get('people'))}):")
                    for person in results.get("people"):
                        socials = [social for social in person.get("socials").values() if social is not None]
                        print(f"\t{person.get('name')}, {person.get('role')}{', ' + ', '.join(socials) if socials else ''}")
                        if org_spy.descriptions:
                            if person.get("description"):
                                desc = textwrap.fill(person.get('description').replace('\n',''), width=shutil.get_terminal_size()[0] - 50, initial_indent='', subsequent_indent='\t\t')
                                print(f"\t\t{desc}\n")
                            else:
                                print()
            else:
                print("No matches :(")
    
    except Exception as ex:
        print(ex)