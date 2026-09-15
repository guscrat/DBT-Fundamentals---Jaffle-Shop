with

source as (

    select * from {{ source('jaffle_shop', 'orders') }}

),

renamed as (

    select
        id as order_id,
        user_id as customer_id,
        cast(order_date as date) as order_date,
        status

    from source

)

select * from renamed