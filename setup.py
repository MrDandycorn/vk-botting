from setuptools import setup
import re

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

version = ''
with open('vk_botting/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    try:
        import subprocess

        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

readme = ''
with open('README.md') as f:
    readme = f.read()

extras_require = {
    'docs': [
        'sphinx==3.0.3',
        'sphinxcontrib_trio==1.1.2',
        'sphinxcontrib-websupport',
    ]
}

setup(name='vk-botting',
      author='MrDandycorn',
      url='https://github.com/MrDandycorn/vk-botting',
      project_urls={
          "Documentation": "https://vk-botting.readthedocs.io/en/latest/",
          "Issue tracker": "https://github.com/MrDandycorn/vk-botting/issues",
      },
      version=version,
      packages=['vk_botting'],
      license='MIT',
      description='A basic package for building async VK bots',
      long_description=readme,
      long_description_content_type="text/markdown",
      include_package_data=True,
      install_requires=requirements,
      extras_require=extras_require,
      python_requires='>=3.6.0',
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Natural Language :: Russian',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Topic :: Internet',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Utilities',
      ]
      )
