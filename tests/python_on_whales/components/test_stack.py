import time
from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.utils import PROJECT_ROOT


@pytest.fixture
def with_test_stack():
    docker.swarm.init()
    docker.stack.deploy(
        "some_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
    )
    time.sleep(1)
    yield
    docker.stack.remove("some_stack")
    time.sleep(1)
    docker.swarm.leave(force=True)
    time.sleep(1)


@pytest.mark.usefixtures("with_test_stack")
def test_services_inspect():
    all_services = docker.service.list()
    assert len(all_services) == 4
    assert set(all_services) == set(docker.stack.services("some_stack"))


def test_stack_variables():
    docker.swarm.init()
    docker.stack.deploy(
        "other_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        variables={"SOME_VARIABLE": "hello-world"},
    )

    agent_service = docker.service.inspect("other_stack_agent")
    expected = "SOME_OTHER_VARIABLE=hello-world"
    assert expected in agent_service.spec.task_template.container_spec.env

    docker.stack.remove("other_stack")
    time.sleep(1)
    docker.swarm.leave(force=True)
    time.sleep(1)


def test_stack_env_files(tmp_path: Path):
    env_file = tmp_path / "some.env"
    env_file.write_text("SOME_VARIABLE=hello-world # some var \n # some comment")
    docker.swarm.init()
    third_stack = docker.stack.deploy(
        "third_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        env_files=[env_file],
    )

    agent_service = docker.service.inspect("third_stack_agent")
    expected = "SOME_OTHER_VARIABLE=hello-world"
    assert expected in agent_service.spec.task_template.container_spec.env

    assert docker.stack.list() == [third_stack]
    time.sleep(1)
    docker.stack.remove(third_stack)
    time.sleep(1)
    docker.swarm.leave(force=True)
    time.sleep(1)