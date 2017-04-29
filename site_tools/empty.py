def generate(env):
    env['WHOAMI'] = 'I am minimal environment'

def exists(env):
    return find(env)
