output "raw_bucket" { value = module.storage.raw_bucket }
output "vector_bucket_name" { value = module.storage.vector_bucket_name }
output "vector_index_name" { value = module.storage.vector_index_name }
output "api_url" { value = module.api.api_url }
output "site_url" { value = "https://${module.frontend.domain}" }
