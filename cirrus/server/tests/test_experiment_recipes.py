from cirrus.experiment_recipes import RemoteSetting


def test_get_recipes_empty():
    rs = RemoteSetting()
    assert rs.get_recipes() == []


def test_update_recipes():
    rs = RemoteSetting()
    new_recipes = [{"experiment1": True}, {"experiment2": False}]
    rs.update_recipes(new_recipes)
    assert rs.get_recipes() == new_recipes
