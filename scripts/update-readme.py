#!/usr/bin/env python3
import sexpdata
import io
from sexpdata import Symbol
from pathlib import Path
from enum import Enum

script_dir = Path(__file__).parent
project_dir = (script_dir / '..').resolve()

def parse_kicad_sym(path):
    result = {}
    with io.open(path, 'r', encoding='utf-8') as dcm:
        top = sexpdata.load(dcm)
        assert(top[0] == Symbol('kicad_symbol_lib'))
        for symbol in [s for s in top[1:] if s[0] == Symbol('symbol')]:
            comp = None
            datasheet = ''
            description = ''
            for prop in [p for p in symbol[1:] if p[0] == Symbol('property')]:
                if prop[1] == "Value":
                    comp = prop[2]
                elif prop[1] == "Datasheet":
                    datasheet = prop[2]
                elif prop[1] == "Description":
                    description = prop[2]
            if comp is not None:
                result[comp] = (description, '' if datasheet == '' or datasheet == '~' else f'[Datasheet]({datasheet})')
    return result

def generate_symbol_table():
    result = {}
    for path in project_dir.glob('*.kicad_sym'):
        result.update(parse_kicad_sym(path))
    return sorted([(comp, description, datasheet) for comp, (description, datasheet) in result.items()], key=lambda symbol: symbol[0])

def generate_footprint_table():
    wrls = {}
    for path in project_dir.glob('*.3dshapes/*.wrl'):
        key = '{}/{}'.format(path.parent.stem, path.stem)
        wrls[key] = True

    steps = {}
    for path in project_dir.glob('*.3dshapes/*.step'):
        key = '{}/{}'.format(path.parent.stem, path.stem)
        steps[key] = True

    result = []
    for path in project_dir.glob('*.pretty/*.kicad_mod'):
        key = '{}/{}'.format(path.parent.stem, path.stem)
        result.append((path.stem, key in wrls, key in steps))
    return sorted(result, key=lambda footprint: footprint[0])

photos = {}
for path in project_dir.glob('photos/*.jpg'):
    photos[path.stem] = path.relative_to(project_dir)

symbol_table = generate_symbol_table()
fp_table = generate_footprint_table()

State = Enum('State', 'passthrough symbols footprints')

state = State.passthrough
with io.StringIO() as buf:
    with io.open(project_dir / "README.markdown", 'r', encoding='utf-8') as readme:
        for raw_line in readme:
            line = raw_line.strip()
            if state == State.passthrough:
                print(line, file=buf)
                if line.startswith('<!-- SYMBOLS START'):
                    state = State.symbols
                elif line.startswith('<!-- FOOTPRINTS START'):
                    state = State.footprints
            elif state == State.symbols:
                if line.startswith('<!-- SYMBOLS END'):
                    print('| Name | Description | Datasheet |', file=buf)
                    print('| - | - | - |', file=buf)
                    for (name, description, datasheet) in symbol_table:
                        photo = photos.get(name)
                        if photo:
                            photo = '![{}]({})'.format(name, photo)
                        print('| {} | {} | {} |'.format('{} <br> {}'.format(name, photo) if photo else name, description, datasheet), file=buf)
                    print(line, file=buf)
                    state = State.passthrough
            elif state == State.footprints:
                if line.startswith('<!-- FOOTPRINTS END'):
                    print('| Name | WRL 3D model | STEP 3D model |', file=buf)
                    print('| - | - | - |', file=buf)
                    for (name, wrl, step) in fp_table:
                        photo = photos.get(name)
                        if photo:
                            photo = '![{}]({})'.format(name, photo)
                        print('| {} | {} | {} |'.format('{} <br> {}'.format(name, photo) if photo else name, ':heavy_check_mark:' if wrl else '', ':heavy_check_mark:' if step else ''), file=buf)
                    print(line, file=buf)
                    state = State.passthrough
            else:
                raise ValueError('invalid state {}'.format(state))
    with io.open(project_dir / "README.markdown", 'w', encoding='utf-8') as readme:
        readme.write(buf.getvalue())
