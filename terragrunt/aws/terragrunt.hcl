include "root" {
  path = find_in_parent_folders()
  expose = true # Needed to read locals from root config
}

terraform {
  source = include.root.locals.source_base_url
}
