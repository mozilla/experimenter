from cirrus.experiment_recipes import RemoteSettings


def test_get_recipes_is_empty():
    rs = RemoteSettings()
    assert rs.get_recipes() == []


def test_update_recipes():
    rs = RemoteSettings()
    new_recipes = [{"experiment1": True}, {"experiment2": False}]
    rs.update_recipes(new_recipes)
    assert rs.get_recipes() == new_recipes
