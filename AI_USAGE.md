# AI-Assisted Development Documentation

## AI Tools Used
- Claude - Sonnet 4.6
- DeepSeek 

## Prompts Given

### Initial Prompt: 
Let us create a Django project. Here are the requirements:
When a customer places an order on an e-commerce app, the warehouse team needs to know which shipping box should be used. Each product has dimensions and weight. Each box has internal dimensions, maximum weight capacity, and cost.
Your task is to design and build a small Django-based system that recommends the most suitable box for an order.
This has to be submitted as a GitHub link and a zip file. 
There should also be test cases.
Test run output: GitHub Actions link


First we will decide what pages we will have with what functionality, and the tech stack to use alongside. 



You can suggest something better. Here is my idea. 

1. This assignment is in context of an e-commerce company, but doesnt explicitly say an e-commerce app must also be created. This seems to be an internal app used by the warehouse team. So this functionality can be a feature used in the app. 
2. For database, Postgres can be used
3. Deployment is not asked for, but it should be done for quality. I have a free aws account we can use. 
4. We should have login functionality.  And user types if relevant or needed
5. frontend stack is not specified. we can use Django templating language for frontend. 
6. This is a time bound assignment, with 24 hours limit. 

My understanding is this. 
this Django app will take as input an order placed by a customer. It will analyse the items in the order and suggest a box. We should also have a list of box dimensions we have available. An order should be sent in a single box. 
Each order should also have statuses like 'order dispatched', 'to be packed', 'packed', etc. so we can show on the index page. 

We will make the assignment step by step.

#### Follow up prompt :
Q: For the box-fitting algorithm, should we use simple bounding-box volume (fast, explainable) or attempt a more realistic 3D bin-packing approach (complex, slower)?
A: Simple bounding box — good enough for a warehouse tool
Q: For AWS deployment, what's your preference?
A: Skip deployment for now, focus on code quality
Q: Should orders be created manually in this app (warehouse staff enters them), or seeded via fixtures/admin for demo purposes?
A: Both




## Output Accepted

The code files, the algorithm, test suite and ci files.


## Rejected and modified output 

Several files were refactored and modified.
1. The directory structure was followed from django documentation instead of the AI's suggested one. 
2. Changed Python and Django versions
3. Fixed template files where name field was being wrongly used 
4. Fixed how fixtures are to be used and changed location in the directory
5. fixed test case to use Decimal instead due to compatibility issues with newer python versions.


## Mistakes made by AI

AI made mistakes in directory structure, paths and did not setup the postgres DB consistently across the project, other than making mistakes in django form fields. 


## Verification of final code

I ran the application in my local mac, and tested out each page manually first before running the test suite as well.
After initial manual testing, I ran automated tests and integrated to Github actions.
Henceforth, each push would be verified automatically by github actions that runs the test suite. 


## Links to transcripts 

1. https://chat.deepseek.com/share/64tm4anvtxls0kibyf

2. https://claude.ai/share/3dbcda39-c558-41dd-a1c6-21b47442a867

### PDF format 

[Claude Transcript](./Django%20shipping%20box%20recommendation%20system%20-%20Claude.pdf)

[DeepSeek Transcript](./Django%20Project%20Setup%20-%20Transcript%201.pdf)