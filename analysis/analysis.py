# Load f.json
# Data can contain duplicates, so please remove ones before any calculation
# f.json has the following sample structure:
data_schema = [
  {
    "id": 1,
    "owner": "user2",
    "price": 8647,
    "category": "cat1"
  },
  ...
]

# Requirements
# 1. Calculate number of items sold in each category
# 2. Calculate total sum of sells for each category

# Reference results
# {'cat1': 333103, 'cat3': 333386, 'cat2': 333511}
# {'cat1': 1831348772, 'cat3': 1832844186, 'cat2': 1832867646}

