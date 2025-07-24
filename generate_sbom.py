# generate_sbom.py

import os
import sys
import json
import subprocess
import datetime
from typing import List

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model.metadata import Metadata, Tool
from cyclonedx.model.dependency import Dependency
from cyclonedx.output import get_instance, OutputFormat

def detect_languages(path=".") -> List[str]:
    langs = []
    files = os.listdir(path)
    if "package.json" in files:
        langs.append("node")
    if "pom.xml" in files or "build.gradle" in files:
        langs.append("java")
    if "requirements.txt" in files or any(f.endswith(".py") for f in files):
        langs.append("python")
    return langs

def get_python_components():
    import pkg_resources
    components = []
    dependencies = []
    for dist in pkg_resources.working_set:
        comp = Component(
            name=dist.project_name,
            version=dist.version,
            type=ComponentType.LIBRARY
        )
        components.append(comp)
        dep = Dependency(ref=comp.bom_ref)
        dependencies.append(dep)
    return components, dependencies

def get_node_sbom():
    print("[*] Running cyclonedx-npm for Node.js...")
    result = subprocess.run(["cyclonedx-npm", "--output-file", "bom-node.json"], capture_output=True)
    if result.returncode != 0:
        print("[-] Failed to generate Node.js SBOM")
    else:
        print("[+] Node.js SBOM saved as bom-node.json")

def get_java_sbom():
    print("[*] Running Maven plugin for Java...")
    result = subprocess.run(["mvn", "org.cyclonedx:cyclonedx-maven-plugin:makeBom"], capture_output=True)
    if result.returncode != 0:
        print("[-] Failed to generate Java SBOM")
    else:
        print("[+] Java SBOM saved under target/")

def build_python_bom(components, dependencies) -> Bom:
    bom = Bom()
    bom.metadata = Metadata(
        timestamp=datetime.datetime.utcnow(),
        tools=[Tool(vendor="YourOrg", name="CustomSBOMGen", version="1.0")]
    )
    bom.components = components
    bom.dependencies = dependencies
    return bom

def save_bom(bom: Bom, filename: str):
    outputter = get_instance(bom=bom, output_format=OutputFormat.JSON)
    with open(filename, "w") as f:
        f.write(outputter.output_as_string())
    print(f"[+] SBOM saved to {filename}")

def main():
    print("[*] Detecting languages...")
    langs = detect_languages()
    print(f"[+] Detected: {', '.join(langs)}")

    if "python" in langs:
        print("[*] Generating Python SBOM...")
        components, dependencies = get_python_components()
        bom = build_python_bom(components, dependencies)
        save_bom(bom, "bom.1.2.json")

    if "node" in langs:
        get_node_sbom()  # Requires cyclonedx-npm to be installed

    if "java" in langs:
        get_java_sbom()  # Requires Maven + plugin in pom.xml

if __name__ == "__main__":
    main()
