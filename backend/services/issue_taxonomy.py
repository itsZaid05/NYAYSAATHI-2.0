"""Factual triage rubric. These are research topics, not findings of liability."""

ISSUE_RUBRIC = {
    "defective_product": "An alleged fault in goods, including when a coverage/repair dispute also exists. Do not assume the cause or that the seller is liable.",
    "refund_refusal": "A requested, promised or disputed return of money is withheld, reduced or replaced by credit. Payment alone or a missed service alone is insufficient; an unrequested refund is only a possible remedy, not a stated dispute.",
    "misleading_advertising": "A disputed pre-transaction representation, price disclosure or mismatch between an advertised promise and supplied terms/performance. Ordinary dissatisfaction or failure to perform a contract/cover promise alone is insufficient; establish the disputed pre-transaction representation.",
    "subscription_billing": "A disputed recurring debit, renewal consent, cancellation or ongoing membership billing. A single purchase alone is insufficient.",
    "warranty": "A dispute about a stated repair, cover, guarantee or protection promise, including its performance or exclusions. Goods being faulty alone does not establish a coverage promise.",
    "online_shopping": "Explicit digital ordering/checkout, marketplace or app purchase context that needs e-commerce research. This is a transaction-channel facet, not an additional finding of wrongdoing or proof of consumer standing. Do not infer online from a seller name, delivery, saved advertising or the digital nature of content alone; the ordering/checkout/app transaction context must be stated.",
    "service_deficiency": "An alleged non-delivery, delay or shortfall in a purchased service, distinct from the treatment of any money-back request. A physical product fault alone is insufficient.",
    "other_consumer": "A distinct disputed consumer-transaction concern not covered above. Do not add this as a redundant catch-all.",
}
