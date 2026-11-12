TOPIC = "How to plan a weekly meal prep routine"

EVIDENCE = [
    ("Start with your calendar", "Plan meals around the nights you have time to cook. Choose a smaller number of meals and leave a flexible slot for leftovers or changed plans."),
    ("Build a reusable grocery list", "Check your pantry before shopping. Group ingredients by store section and choose recipes with overlapping ingredients so each purchase has a clear purpose."),
    ("Prep ingredients in batches", "Batch shared tasks, such as chopping vegetables or preparing a sauce. Keep toppings and dressings separate until serving for more flexibility."),
    ("Review your plan each week", "Keep track of what was eaten and what was left over. Use that information to adjust portions, shopping, and the time you set aside for prep."),
]


def fixtures():
    return [
        dict(rank=rank, title=EVIDENCE[rank - 1][0] if rank <= 4 else f"Sample result {rank}",
             url=f"https://example.org/meal-prep/{rank}",
             status="Reviewed" if rank <= 4 else "Snippet only" if rank <= 7 else "Unavailable",
             **({"text": EVIDENCE[rank - 1][1]} if rank <= 4 else {}))
        for rank in range(1, 11)
    ]


def article():
    return dict(title="How to Plan a Weekly Meal Prep Routine", seo_title="How to Plan Weekly Meal Prep",
                meta_description="Plan a week of meals around your schedule, shop with a focused list, and prep flexible ingredients in one session.",
                body=BODY.strip())


BODY = """
A weekly meal prep routine starts with your calendar. Pick a few meals that fit the time you actually have, write one grocery list, and use a single session to tackle the steps those meals share. Leave a night open for leftovers or a change of plans. [1] For your first week, try planning three dinners and building the rest of the routine around them.

## Pick the nights that need a plan

Look at the coming week before opening a recipe app. If Tuesday is packed and Thursday is free, choose something quick to assemble for Tuesday and save the meal that takes more attention for Thursday. [1] Write down where you expect to eat each night, including evenings when you already have plans. That gives you a realistic number of meals to shop for.

Give each planned dinner a job. One can be the meal you look forward to, another can be the one you put together when you get home late, and a third can use ingredients you already own. If you usually order food on Friday, decide whether that belongs in this week's plan. A routine should fit the way you spend your week.

## Shop for meals that share ingredients

Open your fridge and cupboards before making your list. Check how much you already have of anything your recipes call for, then group the remaining items by store section. Recipes that share ingredients give you more ways to use what you buy. [2] For example, pick cabbage for a rice bowl and use the rest in tacos. Put both uses on your plan so you remember why it is there.

On paper or in your phone, write the quantity beside each ingredient. If the store sells something in a bigger package than you need, decide what you want to do with the extra before buying it. You could swap it into another dinner or choose an ingredient you already have. Keep the list handy when you cook so you can make notes for the next trip.

## Set aside one prep session

Read your recipes together and look for repeated tasks. If two dinners use sliced onions, do that chopping once. If a dressing goes with both meals, make it during the same session and keep it separate until you serve. Batching shared steps and holding back toppings gives you more options at dinner. [3]

Decide how far you want to go before you start. You could prep vegetables and make a sauce, then cook the main dish on the evening you plan to eat it. Or you could spend the session preparing a complete dinner for a busy night. Write down which steps you will finish later, so you can see at a glance how much work each meal still needs.

Put the ingredients for the first dinner together where you will see them. Label any similar containers with the meal they belong to. Before you put away your tools, check the plan and make sure the next meal has everything you need. If an ingredient is missing, choose a substitute while you still have time to think.

## Make the plan easy to change

Keep one dinner flexible. If you have enough of Monday's meal for another serving, use it on the open night. If you get invited out, move the planned meal to a later slot when it still makes sense to use the ingredients. [1] You can also pick a backup dinner from things you keep on hand, such as pasta with a pantry sauce.

Shared ingredients can help here, too. Keep a dressing on the side and decide whether to use it on a salad or a grain bowl when you eat. [3] If someone at home prefers a different topping, let them add it at the table. Think of the plan as a short list of meals and ingredients you can rearrange as the week unfolds.

## Review what actually happened

Before making the next list, look at what got eaten, what remained, and which tasks took more time than you expected. Use those observations to change your portions or how much prep you schedule. [4] If you kept skipping a meal because it required too many steps after work, try a simpler option for that time slot next week.

Keep the part of the routine that worked. You might repeat a dinner everyone liked, shop with the same list format, or move your prep session to a quieter day. Change one part at a time so you can tell what made the week easier. After a few rounds, you will have a set of meals and prep steps you can pull from whenever you need a plan.

To get started today, choose three dinner nights, write down one shared ingredient, and pick a time to prep it. When you make next week's plan, check how that first session fit your schedule.
"""
