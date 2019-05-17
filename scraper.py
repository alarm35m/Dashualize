
#####################################################
##### Function for Transform searching keywords #####
#####################################################
# The default "quote = False"
def transform(input,sign, quote = False):
    syntax = input.replace(" ", sign)
    if quote == True:
        syntax = ''.join(['"', syntax, '"'])
    return(syntax)

#####################################################
##### Function to Scrape Indeed #####
#####################################################
def scrapeindeed(input_job):

    import bs4
    import numpy
    import pandas
    import re
    import requests
    import datetime
    import stop_words
    
    ###################################################
    #################### ARGUMENTS ####################
    ###################################################
    #input_job = "Deep Learning"
    input_quote = False # add quotation marks("") to your input_job
    input_city = "" # leave empty if input_city is not specified
    input_state = ""
    sign = "+"
    BASE_URL_indeed = 'http://www.indeed.com'

    ######################################
    ########## Generate the URL ##########
    ######################################
    if not input_city: # if (input_city is "")
        url_indeed_list = [ BASE_URL_indeed, '/jobs?q=', transform(input_job, sign, input_quote),
                        '&l=', input_state]
        url_indeed = ''.join(url_indeed_list)
    else: # input_city is not ""
        url_indeed_list = [ BASE_URL_indeed, '/jobs?q=', transform(input_job, sign, input_quote),
                        '&l=', transform(input_city, sign), '%2C+', input_state]
        url_indeed = ''.join(url_indeed_list)
    print(url_indeed)

    # get the HTML code from the URL
    rawcode_indeed = requests.get(url_indeed)
    # Choose "lxml" as parser
    soup_indeed = bs4.BeautifulSoup(rawcode_indeed.text, "lxml")

    # total number of results
    num_total_indeed = soup_indeed.find(
                            id = 'searchCount').contents[0].split()[-2]
    num_total_indeed = re.sub("[^0-9]","", num_total_indeed) # remove non-numeric characters in the string
    num_total_indeed = int(num_total_indeed)
    print(num_total_indeed)

    # total number of pages
    num_pages_indeed = int(numpy.ceil(num_total_indeed/10.0))
    print(num_pages_indeed)

    # create an empty dataframe
    job_df_indeed = pandas.DataFrame()
    # the date for today
    now = datetime.datetime.now()
    now_str = now.strftime("%m/%d/%Y")
    now_str_name=now.strftime('%m%d%Y')

    ########################################
    ##### Loop for all the total pages #####
    ########################################

    if num_pages_indeed > 100:
        num_pages_indeed = 50

    for i in range(1, num_pages_indeed+1):
        # generate the URL
        url = ''.join([url_indeed, '&start=', str(i*10)])
        print(url)

        # get the HTML code from the URL
        rawcode = requests.get(url)
        soup = bs4.BeautifulSoup(rawcode.text, "lxml")

        # pick out all the "div" with "class="job-row"
        divs = soup.findAll("div")
        job_divs = [jp for jp in divs if not jp.get('class') is None
                        and 'row' in jp.get('class')]

        # loop for each div chunk
        for job in job_divs:
            try:
                # job id
                id = job.get('data-jk', None)
                # job link related to job id
                link = BASE_URL_indeed + '/rc/clk?jk=' + id
                # job location
                location = job.find('span', {'class': 'location'}).text.strip()
                location = location.split(', ')
                city = location[0]
                state = location[1][0:2]

            except:
                continue

            job_df_indeed = job_df_indeed.append({'job_id': id,
                                    'City':city,
                                    'State':state,
                                    'job_link':link},ignore_index=True)

    cols=['job_id','City','State','job_link']
    job_df_indeed = job_df_indeed[cols]
    print(job_df_indeed.shape)

    # delete the duplicated jobs using job link
    job_df_indeed = job_df_indeed.drop_duplicates(['job_link'], keep='first')

    # print the dimenstion of the dataframe
    print(job_df_indeed.shape)

    ############################################################################
    ##### Define the terms that I am interested and would like to pick out #####
    ############################################################################

    # define the stop_words for future use
    stop_words = stop_words.get_stop_words('english') # list out all the English stop word

    job_df_indeed_skills = pandas.DataFrame()
    job_df_indeed_experience = pandas.DataFrame()
    job_df_indeed_soft_skills = pandas.DataFrame()

    ##### Job types #####
    type = ['Entry','Skilled','Expert']
    type_lower = [s.lower() for s in type] # lowercases
    # map the type_lower to type
    type_map = pandas.DataFrame({'raw':type, 'lower':type_lower}) # create a dataframe
    type_dic = list(type_map.set_index('lower').to_dict().values()).pop() # use the dataframe to create a dictionary
    # print(type_dic)

    ##### Skills #####
    skills = ['Python','R','SQL','Spark','Hadoop','Java','SAS','Tableau','Hive','Scala','C++','AWS','TensorFlow',
              'Matlab','C','Excel','Linux','NoSQL','Azure','Scikit-learn','SPSS','Pandas','Numpy','Pig','D3',
              'Keras','Javascript','C#','Perl','Hbase','Docker','Git','MySQL','MongoDB','Cassandra','PyTorch','Caffe']
    skills_lower = [s.lower() for s in skills]# lowercases
    skills_map = pandas.DataFrame({'raw':skills, 'lower':skills_lower})# create a dataframe
    skills_dic = list(skills_map.set_index('lower').to_dict().values()).pop()# use the dataframe to create a dictionary
    # print(skills_dic)

    ##### Soft Skills #####
    soft_skills = ['artificial intelligence','communication','machine learning','computer science','statistics','data analysis','visualization',
                   'AI composite','software development','presentation','deep learning','project management','math',
                   'software engineering','NLP composite','devops','neural networks']
    soft_skills_lower = [s.lower() for s in soft_skills]# lowercases
    soft_skills_map = pandas.DataFrame({'raw':soft_skills, 'lower':soft_skills_lower})# create a dataframe
    soft_skills_dic = list(soft_skills_map.set_index('lower').to_dict().values()).pop()# use the dataframe to create a dictionary
    # print(skills_dic)

    ##############################################
    ##### For Loop for scraping each job URL #####
    ##############################################
    # empty list to store details for all the jobs
    list_type = []
    list_skill = []
    list_soft_skill = []

    for i in range(len(job_df_indeed)):

        try:
            # get the HTML code from the URL
            job_page = requests.get(job_df_indeed.iloc[i, 3])
            # Choose "lxml" as parser
            soup = bs4.BeautifulSoup(job_page.text, "lxml")

            # drop the chunks of 'script','style','head','title','[document]'
            for elem in soup.findAll(['script','style','head','title','[document]']):
                elem.extract()
            # get the lowercases of the texts
            texts = soup.getText(separator=' ').lower()

            # cleaning the text data
            string = re.sub(r'[\n\r\t]', ' ', texts) # remove "\n", "\r", "\t"
            string = re.sub(r'\,', ' ', string) # remove ","
            string = re.sub('/', ' ', string) # remove "/"
            string = re.sub(r'\(', ' ', string) # remove "("
            string = re.sub(r'\)', ' ', string) # remove ")"
            string = re.sub(' +',' ',string) # remove more than one space
            string = re.sub(r'r\s&\sd', ' ', string) # avoid picking 'r & d'
            string = re.sub(r'r&d', ' ', string) # avoid picking 'r&d'
            string = re.sub('\.\s+', ' ', string) # remove "." at the end of sentences

            # Job types
            for typ in type_lower :
                if any(x in typ for x in ['+', '#', '.']):
                    typp = re.escape(typ) # make it possible to find out 'c++', 'c#', 'd3.js' without errors
                else:
                    typp = typ
                result = re.search(r'(?:^|(?<=\s))' + typp + r'(?=\s|$)', string) # search the string in a string
                if result:
                    list_type.append(type_dic[typ])
                    job_df_indeed_experience = job_df_indeed_experience.append({'Pay Range': type_dic[typ]}
                                                                               ,ignore_index=True)

            # Skills
            for sk in skills_lower :
                if any(x in sk for x in ['+', '#', '.']):
                    skk = re.escape(sk)
                else:
                    skk = sk
                result = re.search(r'(?:^|(?<=\s))' + skk + r'(?=\s|$)',string)
                if result:
                    list_skill.append(skills_dic[sk])
                    job_df_indeed_skills = job_df_indeed_skills.append({'Tech Skills': skills_dic[sk]},
                                                                       ignore_index=True)

            # Soft Skills
            for sk in soft_skills_lower :
                if any(x in sk for x in ['+', '#', '.']):
                    skk = re.escape(sk)
                else:
                    skk = sk
                result = re.search(r'(?:^|(?<=\s))' + skk + r'(?=\s|$)',string)
                if result:
                    list_soft_skill.append(soft_skills_dic[sk])
                    job_df_indeed_soft_skills = job_df_indeed_soft_skills.append({'Soft Skills': soft_skills_dic[sk]},
                                                                       ignore_index=True)

        except:
            list_type.append('Forbidden')
            list_skill.append('Forbidden')
            list_soft_skill.append('Forbidden')
        print(i)

    #keeping only from and location
    job_df_indeed.drop(['job_id','job_link'], axis=1)
    cols=['City','State']
    job_df_indeed = job_df_indeed[cols]

    # print the dimenstion of the dataframe
    print(job_df_indeed.shape)

    job_df_indeed_info = pandas.DataFrame()

    if len(job_df_indeed_skills) > len(job_df_indeed_soft_skills):
        for i in range(len(job_df_indeed_skills)):
            job_df_indeed_info = job_df_indeed_info.append({'Keyword':input_job, 'Job Board':'Indeed'},ignore_index=True)
    else:
        for i in range(len(job_df_indeed_soft_skills)):
            job_df_indeed_info = job_df_indeed_info.append({'Keyword':input_job, 'Job Board':'Indeed'},ignore_index=True)

    result = pandas.concat([job_df_indeed_info, job_df_indeed_skills], axis = 1)
    result = pandas.concat([result, job_df_indeed_soft_skills], axis = 1)
    result = pandas.concat([result, job_df_indeed], axis = 1)
    result = pandas.concat([result, job_df_indeed_experience], axis = 1)
    
    if len(job_df_indeed_experience) > 0:
        cols=['Keyword','Job Board','Tech Skills','Soft Skills','City','State','Pay Range']
    else:
        cols=['Keyword','Job Board','Tech Skills','Soft Skills','City','State']
        
    result = result[cols]
    return result

#####################################################
##### Function to Scrape CareerBuilder #####
#####################################################
def scrapecareerbuilder(input_job):
    
    import bs4
    import numpy
    import pandas
    import re
    import requests
    import datetime
    import stop_words

    ###################################################
    #################### ARGUMENTS ####################
    ###################################################
    #input_job = "Artificial Intelligence"
    input_quote = False # add quotation marks("") to your input_job
    input_city = "" # leave empty if input_city is not specified
    input_state = ""
    sign = "-"
    BASE_URL_careerbuilder = 'http://www.careerbuilder.com'
    
    ######################################
    ########## Generate the URL ##########
    ######################################
    if not input_city: # if (input_city is "")
        url_careerbuilder_list = [ BASE_URL_careerbuilder, '/jobs-',
            transform(input_job, sign, input_quote), '-in-',input_state]
        url_careerbuilder = ''.join(url_careerbuilder_list)
    else: # input_city is not ""
        url_careerbuilder_list = [ BASE_URL_careerbuilder, '/jobs-',
            transform(input_job, sign, input_quote), '-in-',
            transform(input_city, sign),',', input_state]
        url_careerbuilder = ''.join(url_careerbuilder_list)
    print(url_careerbuilder)

    # get the HTML code from the URL
    rawcode_careerbuilder = requests.get(url_careerbuilder)
    # Choose "lxml" as parser
    soup_careerbuilder = bs4.BeautifulSoup(rawcode_careerbuilder.text, "lxml")

    # total number of results
    num_total_careerbuilder = soup_careerbuilder.find(
                                'div', {'class' : 'count'}).contents[0]
    print(num_total_careerbuilder)
    num_total_careerbuilder = int(re.sub('[\(\)\{\}<>]', '',
                                num_total_careerbuilder).split()[0])
    print(num_total_careerbuilder)

    # total number of pages
    num_pages_careerbuilder = int(numpy.ceil(num_total_careerbuilder/25.0))
    print(num_pages_careerbuilder)

    # create an empty dataframe
    job_df_careerbuilder = pandas.DataFrame()
    # the date for today
    now = datetime.datetime.now()
    now_str = now.strftime("%m/%d/%Y")
    now_str_name=now.strftime('%m%d%Y')

    ########################################
    ##### Loop for all the total pages #####
    ########################################

    if num_pages_careerbuilder > 45:
        num_pages_careerbuilder = 45
        
    for i in range(1, num_pages_careerbuilder+1):
        # generate the URL
        url = ''.join([url_careerbuilder,'?page_number=', str(i)])
        print(url)

        # get the HTML code from the URL
        rawcode = requests.get(url)
        soup = bs4.BeautifulSoup(rawcode.text, "lxml")

        # pick out all the "div" with "class="job-row"
        divs = soup.findAll("div")
        job_divs = [jp for jp in divs if not jp.get('class') is None
                                and 'job-row' in jp.get('class')]

        # loop for each div chunk
        for job in job_divs:
            try:
                # job id
                id = job.find('h2',{'class' : 'job-title'}).find('a').attrs['data-job-did']
                # job link related to job id
                link = BASE_URL_careerbuilder + '/job/' + id            
                # job location
                location = job.find('div', {'class' : 'columns end large-2 medium-3 small-12'}).find(
                            'h4', {'class': 'job-text'}).text.strip()
                
                location = location.split(', ')            
                city = location[0]
                state = location[1][0:2]
                
            except:
                continue

            job_df_careerbuilder = job_df_careerbuilder.append({'job_id': id,
                                    'City':city,
                                    'State':state,
                                    'job_link':link},ignore_index=True)
    cols=['job_id','City','State','job_link']
    job_df_careerbuilder = job_df_careerbuilder[cols]
    print(job_df_careerbuilder.shape)

    # delete the duplicated jobs using job link
    job_df_careerbuilder = job_df_careerbuilder.drop_duplicates(['job_link'], keep='first')

    # print the dimenstion of the dataframe
    print(job_df_careerbuilder.shape)


    # define the stop_words for future use
    stop_words = stop_words.get_stop_words('english') # list out all the English stop word
 
    # read the csv file
    
    job_df_careerbuilder_skills = pandas.DataFrame()
    job_df_careerbuilder_experience = pandas.DataFrame()
    job_df_careerbuilder_soft_skills = pandas.DataFrame()

    ####################################################
    ##### DEFINE THE TERMS THAT I AM INTERESTED IN #####
    ####################################################

    ##### Job types #####
    type = ['Entry','Skilled','Expert']
    type_lower = [s.lower() for s in type] # lowercases
    # map the type_lower to type
    type_map = pandas.DataFrame({'raw':type, 'lower':type_lower}) # create a dataframe
    type_dic = list(type_map.set_index('lower').to_dict().values()).pop() # use the dataframe to create a dictionary
    # print(type_dic)

    ##### Skills #####
    skills = ['Python','R','SQL','Spark','Hadoop','Java','SAS','Tableau','Hive','Scala','C++','AWS','TensorFlow',
              'Matlab','C','Excel','Linux','NoSQL','Azure','Scikit-learn','SPSS','Pandas','Numpy','Pig','D3',
              'Keras','Javascript','C#','Perl','Hbase','Docker','Git','MySQL','MongoDB','Cassandra','PyTorch','Caffe']
    skills_lower = [s.lower() for s in skills]# lowercases
    skills_map = pandas.DataFrame({'raw':skills, 'lower':skills_lower})# create a dataframe
    skills_dic = list(skills_map.set_index('lower').to_dict().values()).pop()# use the dataframe to create a dictionary
    # print(skills_dic)

    ##### Soft Skills #####
    soft_skills = ['artificial intelligence','communication','machine learning','computer science','statistics','data analysis','visualization',
                   'AI composite','software development','presentation','deep learning','project management','math',
                   'software engineering','NLP composite','devops','neural networks']
    soft_skills_lower = [s.lower() for s in soft_skills]# lowercases
    soft_skills_map = pandas.DataFrame({'raw':soft_skills, 'lower':soft_skills_lower})# create a dataframe
    soft_skills_dic = list(soft_skills_map.set_index('lower').to_dict().values()).pop()# use the dataframe to create a dictionary
    # print(skills_dic)

    ##############################################
    ##### FOR LOOP FOR SCRAPING EACH JOB URL #####
    ##############################################
    # empty list to store details for all the jobs
    list_type = []
    list_skill = []
    list_soft_skill = []

    for i in range(len(job_df_careerbuilder)):

        try:
            # get the HTML code from the URL
            job_page = requests.get(job_df_careerbuilder.iloc[i, 3])
            # Choose "lxml" as parser
            soup = bs4.BeautifulSoup(job_page.text, "lxml")

            # drop the chunks of 'script','style','head','title','[document]'
            for elem in soup.findAll(['script','style','head','title','[document]']):
                elem.extract()
            # get the lowercases of the texts
            texts = soup.getText(separator=' ').lower()

            # cleaning the text data
            string = re.sub(r'[\n\r\t]', ' ', texts) # remove "\n", "\r", "\t"
            string = re.sub(r'\,', ' ', string) # remove ","
            string = re.sub('/', ' ', string) # remove "/"
            string = re.sub(r'\(', ' ', string) # remove "("
            string = re.sub(r'\)', ' ', string) # remove ")"
            string = re.sub(' +',' ',string) # remove more than one space
            string = re.sub(r'r\s&\sd', ' ', string) # avoid picking 'r & d'
            string = re.sub(r'r&d', ' ', string) # avoid picking 'r&d'
            string = re.sub('\.\s+', ' ', string) # remove "." at the end of sentences

            # Job types
            for typ in type_lower :
                if any(x in typ for x in ['+', '#', '.']):
                    typp = re.escape(typ) # make it possible to find out 'c++', 'c#', 'd3.js' without errors
                else:
                    typp = typ
                result = re.search(r'(?:^|(?<=\s))' + typp + r'(?=\s|$)', string) # search the string in a string
                if result:
                    list_type.append(type_dic[typ])
                    job_df_careerbuilder_experience = job_df_careerbuilder_experience.append({'Pay Range': type_dic[typ]}
                                                                               ,ignore_index=True)
                    
            # Skills
            for sk in skills_lower :
                if any(x in sk for x in ['+', '#', '.']):
                    skk = re.escape(sk)
                else:
                    skk = sk
                result = re.search(r'(?:^|(?<=\s))' + skk + r'(?=\s|$)',string)
                if result:
                    list_skill.append(skills_dic[sk])
                    job_df_careerbuilder_skills = job_df_careerbuilder_skills.append({'Tech Skills': skills_dic[sk]},
                                                                       ignore_index=True)

            # Soft Skills
            for sk in soft_skills_lower :
                if any(x in sk for x in ['+', '#', '.']):
                    skk = re.escape(sk)
                else:
                    skk = sk
                result = re.search(r'(?:^|(?<=\s))' + skk + r'(?=\s|$)',string)
                if result:
                    #required_skills.append(skills_dic[sk])
                    list_soft_skill.append(soft_skills_dic[sk])
                    job_df_careerbuilder_soft_skills = job_df_careerbuilder_soft_skills.append({'Soft Skills': soft_skills_dic[sk]},
                                                                       ignore_index=True)
                    
        except: # to avoid Forbidden webpages
            list_type.append('Forbidden')
            list_skill.append('Forbidden')
            list_soft_skill.append('Forbidden')
        print(i)

    job_df_careerbuilder.drop(['job_id','job_link'], axis=1)
    cols=['City','State']
    job_df_careerbuilder = job_df_careerbuilder[cols]

    # print the dimenstion of the dataframe
    print(job_df_careerbuilder.shape)

    job_df_careerbuilder_info = pandas.DataFrame()

    if len(job_df_careerbuilder_skills) > len(job_df_careerbuilder_soft_skills):
        for i in range(len(job_df_careerbuilder_skills)):
            job_df_careerbuilder_info = job_df_careerbuilder_info.append({'Keyword':input_job, 'Job Board':'CareerBuilder'},ignore_index=True)
    else:
        for i in range(len(job_df_careerbuilder_soft_skills)):
            job_df_careerbuilder_info = job_df_careerbuilder_info.append({'Keyword':input_job, 'Job Board':'CareerBuilder'},ignore_index=True)

    result = pandas.concat([job_df_careerbuilder_info, job_df_careerbuilder_skills], axis = 1)
    result = pandas.concat([result, job_df_careerbuilder_soft_skills], axis = 1)
    result = pandas.concat([result, job_df_careerbuilder], axis = 1)
    result = pandas.concat([result, job_df_careerbuilder_experience], axis = 1)
    if len(job_df_careerbuilder_experience) > 0:
        cols=['Keyword','Job Board','Tech Skills','Soft Skills','City','State','Pay Range']
    else:
        cols=['Keyword','Job Board','Tech Skills','Soft Skills','City','State']
    result = result[cols]
    return result

def main():
    import pandas
    r1 = scrapeindeed("Artificial Intelligence")
    r2 = scrapeindeed("Deep Learning")
    r3 = scrapeindeed("Machine Learning")
    r4 = scrapecareerbuilder("Artificial Intelligence")
    r5 = scrapecareerbuilder("Deep Learning")
    r6 = scrapecareerbuilder("Machine Learning")

    result = pandas.concat([r1,r2], ignore_index="true")
    result = pandas.concat([result,r3], ignore_index="true")
    result = pandas.concat([result,r4], ignore_index="true")
    result = pandas.concat([result,r5], ignore_index="true")
    result = pandas.concat([result,r6], ignore_index="true")
    
    result.to_csv(path)

main()
