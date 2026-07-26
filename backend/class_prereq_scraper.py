import requests
import json
import time

def get_all_compsci_ids():
    print("Fetching master directory of COMPSCI courses...")
    
    # Notice we changed limit=20 to limit=150 in the URL!
    url = "https://app.coursedog.com/api/v1/cm/ucberkeley_peoplesoft/courses/search/%24filters?catalogId=hMSTjIplK6VX5nnJn7ZE&skip=0&limit=150&orderBy=code&formatDependents=false&effectiveDatesRange=2027-05-24%2C2027-05-24&ignoreEffectiveDating=false&ignoreTotalCount=false&columns=customFields.rawCourseId%2CcustomFields.crseOfferNbr%2CcustomFields.catalogAttributes%2CcustomFields.fd9yl%2CcustomFields.repeatRules%2CcustomFields.repeatRuleSpecialCircumstances%2CcustomFields.customOfferingPhrase%2CcustomFields.otherCustomOfferingPhrase%2CcustomFields.customFormat%2CdisplayName%2Cdepartment%2Cdescription%2Cname%2CcourseNumber%2CsubjectCode%2Ccode%2CalternativeCode%2CcourseIdentifier%2CcourseGroupId%2Ccareer%2Ccollege%2ClongName%2Cstatus%2Cinstitution%2CinstitutionId%2Ccredits%2Cdepartments%2CcrossListedCourses"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://undergraduate.catalog.berkeley.edu",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "x-requested-with": "catalog"
    }
    
    # The payload targeting just COMPSCI
    payload = {
        "condition": "AND",
        "filters": [
            {
                "filters": [
                    {"id": "status-course", "condition": "field", "name": "status", "inputType": "select", "group": "course", "type": "is", "value": "Active", "customField": False},
                    {"id": "catalogPrint-course", "condition": "field", "name": "catalogPrint", "inputType": "boolean", "group": "course", "type": "is", "value": True, "customField": False}
                ],
                "id": "QAg3zukO",
                "condition": "and"
            },
            {
                "condition": "AND",
                "filters": [
                    {"group": "course", "id": "subjectCode-course", "inputType": "subjectCodeSelect", "name": "subjectCode", "type": "is", "value": "COMPSCI"}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    course_map = {}
    if "data" in data:
        for item in data["data"]:
            code = item.get("code")
            group_id = item.get("courseGroupId")
            if code and group_id:
                course_map[code] = group_id
                
    print(f"Successfully found {len(course_map)} courses.\n")
    return course_map

def fetch_prerequisites(course_code, group_id):
    # This URL uses dynamic f-string formatting to inject the group_id
    url = f"https://app.coursedog.com/api/v1/cm/ucberkeley_peoplesoft/courses/search/$filters?courseGroupIds={group_id}&effectiveDatesRange=2027-05-24%2C2027-05-24&formatDependents=true&includeRelatedData=true&includeCrosslisted=true&includeCourseEquivalencies=true&includeMappedDocumentItems=false&includePending=false&returnResultsWithTotalCount=false&doNotDisplayAllMappedRevisionsAsDependencies=true"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://undergraduate.catalog.berkeley.edu",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "x-requested-with": "catalog"
    }
    
    payload = {
        "filters": [{"id": "status-course", "condition": "field", "name": "status", "inputType": "select", "group": "course", "type": "is", "value": "Active", "customField": False}],
        "id": "QAg3zukO",
        "condition": "and"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            course_info = data["data"][0]
            requisites = course_info.get("requisites")
            
            print(f"--- {course_code} ---")
            if requisites:
                # We will just print the raw JSON for now so you can see the logic tree
                print("Has Prerequisites: YES")
            else:
                print("Has Prerequisites: NO")
    else:
        print(f"Failed to fetch {course_code}")

if __name__ == "__main__":
    # 1. Get all the IDs
    all_courses = get_all_compsci_ids()
    
    # 2. Convert dictionary to a list so we can slice it
    course_list = list(all_courses.items())
    
    # 3. Loop through ONLY the first 5 courses for testing
    print("Testing prerequisite extraction on the first 5 courses...\n")
    for course_code, group_id in course_list[:5]:
        fetch_prerequisites(course_code, group_id)
        # Sleep for 1 second so we don't get blocked by the server
        time.sleep(1)