import argparse
import yaml
import os
from urllib.parse import urlencode, quote
import webbrowser

parser = argparse.ArgumentParser(description='Generate projects for Things 3 from templates')
parser.add_argument('--options', help='List available template options', default=False, action='store_true')
parser.add_argument('--template', help='The name of the template to create')
parser.add_argument('--title', help='Override the title field in the template')
parser.add_argument('--notes', help='Override the notes field in the template')
parser.add_argument('--deadline', help='Override the deadline field in the template')
parser.add_argument('--when', help='Override the when field in the template')
parser.add_argument('--todo-template', help='A custom todo template string to be used in place of todo items')
parser.add_argument('--todo-start', help='Overrides a template todo start value', type=int)
parser.add_argument('--todo-end', help='Overrides a template todo end value', type=int)
parser.add_argument('--todo-step', help='Overrides a template todo step value', type=int)


def formatFiles(tup):
    fname, description = tup
    fname = fname.split('.')[0]
    return '- {}: {}'.format(fname, description) if description is not None else '- {}'.format(fname)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
# Get the names of all the template files
def getTemplateOptions():
    files = os.listdir(TEMPLATE_PATH)
    descriptions = []
    for f in files:
        with open(os.path.join(TEMPLATE_PATH, f), 'r') as infile:
            s = yaml.load(infile, Loader=yaml.FullLoader)
            descriptions.append(s['description'] if 'description' in s else None)
    return list(map(formatFiles, zip(files, descriptions)))

def renderTodos(todosRaw, args):
    if isinstance(todosRaw, list):
        return todosRaw
    else:
        step = args.todo_step if args.todo_step is not None else todosRaw['step']
        start = args.todo_start if args.todo_start is not None else todosRaw['start']
        end = args.todo_end if args.todo_end is not None else todosRaw['end']
        template = args.todo_template if args.todo_template is not None else todosRaw['template']
        unrolled = [template.format(i, i + step - 1) for i in range(start, end, step)]
        remaining = ((end + 1) - start) % step
        if remaining > 0:
            unrolled.append(template.format((end + 1) - remaining, end))
        if step == 1:
            unrolled.append(template.format(end, end))
        return unrolled

def createThings3Project(template, args):
    renderedTemplateTodos = renderTodos(template['todos'], args)
    projectTemplate = {
        'title': args.title if args.title is not None else template['title'],
        'notes': args.notes if args.notes is not None else template['notes'],
        'area': template['area'],
        'when': args.when if args.when is not None else template['when'],
        'tags': ','.join(template['tags']),
        'deadline': args.deadline if args.deadline is not None else template['deadline'],
        'to-dos': '\n'.join(renderedTemplateTodos),
        'completed': template['completed'],
        'canceled': template['canceled'],
        'reveal': template['reveal'],
        'creation-date': template['creation_date'],
        'completion-date': template['completion_date'],
    }
    params = urlencode({ k: v for k, v in projectTemplate.items() if v is not None }, quote_via=quote)
    success = webbrowser.open_new_tab('things:///add-project?{}'.format(params))
    if not success:
        print('Failed to create new project')

def createThings3Template(template, args):
    supportedTypes = {
        'project': createThings3Project,
    }
    if template['type'] in supportedTypes:
        return supportedTypes[template['type']](template, args)
    else:
        raise Exception('Unknown template type: {}'.format(template.type))


ARGS = parser.parse_args()

if ARGS.template:
    try:
        with open(os.path.join(TEMPLATE_PATH, ARGS.template + '.yml'), 'r') as infile:
            settings = yaml.load(infile, Loader=yaml.FullLoader)
            createThings3Template(settings, ARGS)
    except Exception as e:
        print('Could not load template for "{}"'.format(ARGS.title))
        print(e)

elif ARGS.options:
    print('\n'.join(getTemplateOptions()))
else:
    parser.print_help()
