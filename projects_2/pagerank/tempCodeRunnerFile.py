def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    num_pages = len(corpus)
    initial_val = 1/num_pages

    pagerank = {page : initial_val for page in corpus}

    while True:
        new_pagerank = {}

        # Calculate new PageRank values for each page
        for page in corpus:
            total_rank = (1 - damping_factor) / num_pages
            for other_page in corpus:
                if page in corpus[other_page]:
                    total_rank += damping_factor * (pagerank[other_page] / len(corpus[other_page]))
            new_pagerank[page] = total_rank

        # Check for convergence
        converged = True
        for page in pagerank:
            if abs(new_pagerank[page] - pagerank[page]) > 1e-6:
                converged = False
                break

        if converged:
            break

        pagerank = new_pagerank

    return pagerank